#!/usr/bin/env python3

__author__ = "Pieter Lexis <pieter.lexis@powerdns.com>, William Light <wrl@lhiaudio.com>"
__copyright__ = "Copyright 2018, PowerDNS.COM BV"
__license__ = "Apache 2.0"

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sysrepo as sr
import logging
import sys

from typing import Union, List

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

"""
This script is meant to be run as a pipe-backend script in the PowerDNS Authortiative Server.
It uses the ABI version 2.

pdns.conf should have lines similar to this:

launch=pipe
pipe-abi-version=2
pipe-command=/path/to/pipe-yang-backend.py
"""

class YANGBackend:
    """
    This class is a sysrepo YANG backend. After initializing, run() needs to be called to start the main loop.
    """

    module_name = 'dns-server-amended-with-zone'
    root_xpath = '/{}:dns-server'.format(module_name)
    zones_xpath = '{}/zones'.format(root_xpath)
    zone_xpath = '{}/zone'.format(zones_xpath)

    def __init__(self):
        """
        Sets up a session to the sysrepo datastore
        """
        log.debug("connecting to sysrepo")
        # connect to sysrepo
        conn = sr.Connection("pdns")
        log.info("connected to sysrepo")

        log.debug("starting session")
        # start session
        self.session = sr.Session(conn)
        log.info("session started")

        if log.level == logging.DEBUG:
            self.get_config_data(self.zones_xpath + '//*')

    def run(self):
        """
        This runs the main loop that reads stdin, processes commands and writes data to stdout

        :return: Should never happen
        """
        hadHelo = False
        for line in sys.stdin:
            line = line.strip()
            log.debug('Had line from PowerDNS: %s', line)
            if not hadHelo:
                self.handle_helo(line)
                hadHelo = True
                continue

            request = line.split('\t')

            if len(request) != 7:
                log.warning("PowerDNS sent an unparsable line: %s", line)
                self.write_line('FAIL')
                continue

            kind, qname, qclass, qtype, zoneid, remoteip, localip = request

            qname = qname.lower()

            # FIXME: clarify list of record types
            record_types = ["SOA", "NS", "A", "AAAA", "MX", "CNAME", "TXT"]

            if qtype == "ANY":
                self.handle_record_query(qname, qclass, record_types)
            elif qtype in record_types:
                self.handle_record_query(qname, qclass, [qtype])
            else:
                self.write_line("END")

    def write_line(self, line: str):
        """
        Writes ``line`` to stdout and flushes stdout

        :param str line: The full line to write to stdout
        :return: None
        """
        log.debug("Sending line to PowerDNS: %s", line)
        sys.stdout.write(line)
        sys.stdout.write('\n')
        sys.stdout.flush()

    def handle_helo(self, line) -> None:
        """
        Handles the "HELO" sent by PowerDNS when it launches the backend

        :param line: The line received from PowerDNS
        :return: None
        """
        if not line.startswith('HELO'):
            log.error('Received "%s", expected "HELO"', line)
            self.write_line('FAIL')
            sys.exit(1)

        log.info('received HELO from PowerDNS: %s', line)
        try:
            _, version = line.split('\t')
        except ValueError as e:
            log.error('Malformed HELO message from PowerDNS: %s', line)
            log.debug(e)
            self.write_line('FAIL')
            sys.exit(1)

        log.debug("Received HELO from PowerDNS with version %s", version)

        if int(version) != 2:
            log.error("Wrong pipe-abi-version received (%s), only 2 is supported", version)
            sys.exit(1)

        self.write_line('OK\tYANG backend ready')

    def get_config_data(self, xpath: str) -> Union[None, sr.Vals]:
        """
        Retrieve the configuration data from the datastore at ``xpath``

        :param str xpath: XPATH expression
        :return: None or sysrepo.Vals
        """
        log.debug("Getting config data at '%s'", xpath)

        try:
            values: sr.Vals = self.session.get_items(xpath)
        except RuntimeError as e:
            log.warning("Could not retrieve data for xpath '%s': %s", xpath, e)
            return None

        if log.level == logging.DEBUG:
            if values is None:
                log.debug("Path %s is empty", xpath)
                return None
            log.debug("Got these values for '%s':", xpath)
            for i in range(values.val_cnt()):
                log.debug('\t%s', values.val(i).to_string())

        return values

    def get_domain(self, qname: str) -> Union[None, str]:
        """
        Returns the domain name for the record at `qname`
        """

        # TODO create a domain_id and cache it?
        domain = qname

        while domain != '':
            domain_xpath = '{zone_xpath}[domain="{domain}"]/rrset[type="SOA"]/rdata[text()]'.format(
                zone_xpath=self.zone_xpath,
                domain=domain)
            vals = self.get_config_data(domain_xpath)

            if vals:
                return domain

            domain = '.'.join(domain.split('.')[1:])

        return None

    def handle_record_query(self, qname: str, qclass: str, qtypes: List[str]) -> None:
        """
        Retrieve DNS records from the datastore and write them to stdout using
        the PowerDNS pipe ABI version 2. After writing all of the responses,
        indicates to PowerDNS that there is no more data by writing "END".

        If in doubt about the parameter types, please refer to the PowerDNS
        pipe backend documentation at https://doc.powerdns.com/authoritative/backends/pipe.html

        :param str qname: DNS resource name
        :param str qclass: DNS class
        :param List[str] qtypes: List of DNS record types to retrieve.
            A separate XPath lookup will be performed for each record type.
        :return: None
        """

        # FIXME: we should probably only do this when a change is made.
        #        currently, we have a separate daemon that does that – can we
        #        roll that into this backend? will that cause issues with the
        #        data store updates?
        self.session.refresh()

        domain = self.get_domain(qname)

        if not domain:
            self.write_line("END")
            return

        # TODO return the SOA from self.get_domain and send it to pdns when the
        # qtype is SOA

        record_xpath = '{zone_xpath}[domain="{domain}"]'.format(
                zone_xpath=self.zone_xpath,
                domain=domain)

        # FIXME: we can probably do this all in one XPath query if we're clever
        #        about it
        for qtype in qtypes:
            select_xpath = '{record_xpath}/rrset[type="{qtype}"]/rdata[text()]'.format(
                    record_xpath=record_xpath,
                    qtype=qtype)

            # FIXME: stub/mock for unit testing (this seems like the right
            #        place to do it).
            values = self.get_config_data(select_xpath)

            if not values:
                continue

            # FIXME: get TTL from rrset
            for i in range(values.val_cnt()):
                response = 'DATA\t{qname}\t{qclass}\t{qtype}\t{ttl}\t{id}\t{content}\n'.format(
                        qname=qname, qclass=qclass, qtype=qtype,
                        ttl=3600, id=-1, content=values.val(i).val_to_string())

                # not using `self.write_line()` here to avoid flushing after
                # every line. we'll do that when we write END.
                sys.stdout.write(response)

        self.write_line("END")
        return

def main():
    be = YANGBackend()
    be.run()


if __name__ == "__main__":
    main()
