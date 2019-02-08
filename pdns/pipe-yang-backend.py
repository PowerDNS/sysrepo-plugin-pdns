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

from typing import Union, List, Dict

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

"""
This script is meant to be run as a pipe-backend script in the PowerDNS Authortiative Server.
It uses the ABI version 2.

pdns.conf should have lines similar to this:

launch=pipe
pipe-abi-version=2
pipe-command=/path/to/pipe-yang-backend.py

To support AXFR requests, set 'pipe-abi-version' to 4.
"""

class YANGBackend:
    """
    This class is a sysrepo YANG backend. After initializing, run() needs to be called to start the main loop.
    """

    module_name = 'dns-server-amended-with-zone'
    root_xpath = '/{}:dns-server'.format(module_name)
    zones_xpath = '{}/zones'.format(root_xpath)
    zone_xpath = '{}/zone'.format(zones_xpath)

    abi_version = 0

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
        for line in sys.stdin:
            line = line.strip()
            log.debug('Had line from PowerDNS: %s', line)
            if self.abi_version == 0:
                self.handle_helo(line)
                continue

            request = line.split('\t')

            if self.abi_version == 4 and len(request) == 3:
                kind, zoneid, zonename = request
                if kind == 'AXFR':
                    self.handle_axfr_query(zonename)
                    continue

            if (self.abi_version == 2 and len(request) != 7) or (self.abi_version == 4 and len(request) != 8):
                log.warning("PowerDNS sent an unparsable line: %s", line)
                self.write_line('FAIL')
                continue

            kind, qname, _, qtype, *_ = request
            qname = qname.lower()

            self.handle_record_query(qname, qtype)

    @staticmethod
    def write_line(line: str, flush=True):
        """
        Writes ``line`` to stdout and flushes stdout when flush is True

        :param str line: The full line to write to stdout
        :param bool flush: Whether or not to flush stdout after writing
        :return: None
        """
        log.debug("Sending line to PowerDNS: %s", line)
        sys.stdout.write(line)
        sys.stdout.write('\n')
        if flush:
            sys.stdout.flush()

    def write_rrset(self, rrset: dict, auth: int = 1) -> None:
        for rdata in rrset['rdata']:
            to_write = '{qname}\t{qclass}\t{qtype}\t{ttl}\t{id}\t{content}'.format(
                qname=rrset['owner'], qclass='IN', qtype=rrset['type'],
                ttl=rrset['ttl'], id=-1, content=rdata)
            if self.abi_version == 4:
                to_write = '{subnet_mask}\t{auth}\t{to_write}'.format(
                    subnet_mask=0,
                    auth=auth,
                    to_write=to_write
                )
            self.write_line('DATA\t{to_write}'.format(
                to_write=to_write
            ))

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
            self.abi_version = int(version)
        except ValueError as e:
            log.error('Malformed HELO message from PowerDNS: %s', line)
            log.debug(e)
            self.write_line('FAIL')
            sys.exit(1)

        log.debug("Received HELO from PowerDNS with version %s", self.abi_version)

        if self.abi_version not in [2, 4]:
            log.error("Wrong pipe-abi-version received (%s), only 2 and 4 are supported", self.abi_version)
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
            domain_xpath = '{zone_xpath}[domain="{domain}"]/rrset[type="SOA"][owner="{domain}"]/rdata[text()]'.format(
                zone_xpath=self.zone_xpath,
                domain=domain)
            vals = self.get_config_data(domain_xpath)

            if vals:
                return domain

            domain = '.'.join(domain.split('.')[1:])

        return None

    @staticmethod
    def get_rrset_from_tree(tree: sr.Tree) -> Dict:
        """
        Returns the rrset

        :param sr.Tree tree: A tree rooted at zones/zone/rrset
        :return: A dictionary with the rrset as described in the tree, e.g.:
            {
               'owner': 'www.example.com',
               'ttl': 2400,
               'type': 'A',
               'rdata': ['192.0.2.15', '203.0.113.4']
            }
        """
        ret = dict()

        tree_rrset_vals = tree.first_child()  # type: sr.Tree
        while tree_rrset_vals:
            if tree_rrset_vals.name() == 'rdata':
                if not ret.get(tree_rrset_vals.name()):
                    ret[tree_rrset_vals.name()] = list()
                ret[tree_rrset_vals.name()].append(tree_rrset_vals.data().get_string())
                tree_rrset_vals = tree_rrset_vals.next()
                continue

            if tree_rrset_vals.type() == sr.SR_UINT32_T:
                ret[tree_rrset_vals.name()] = tree_rrset_vals.data().get_uint32()
            if tree_rrset_vals.type() == sr.SR_ENUM_T:
                ret[tree_rrset_vals.name()] = tree_rrset_vals.data().get_enum()
            if tree_rrset_vals.type() == sr.SR_STRING_T:
                ret[tree_rrset_vals.name()] = tree_rrset_vals.data().get_string()

            tree_rrset_vals = tree_rrset_vals.next()

        return ret

    def handle_record_query(self, qname: str, qtype: str) -> None:
        """
        Retrieve DNS records from the datastore and write them to stdout using
        the PowerDNS pipe ABI version 2. After writing all of the responses,
        indicates to PowerDNS that there is no more data by writing "END".

        If in doubt about the parameter types, please refer to the PowerDNS
        pipe backend documentation at https://doc.powerdns.com/authoritative/backends/pipe.html

        :param str qname: DNS resource name
        :param str qclass: DNS class
        :param str qtype: The type of record to retrieve
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

        # TODO return the SOA from self.get_domain and send it to pdns when qtype is SOA

        record_xpath = '{zone_xpath}[domain="{domain}"]/rrset[owner="{qname}"]'.format(
                zone_xpath=self.zone_xpath,
                domain=domain,
                qname=qname)

        if qtype != 'ANY':
            record_xpath = '{record_xpath}[type="{qtype}"]'.format(
                    record_xpath=record_xpath,
                    qtype=qtype)

        log.debug('Attempting to get subtrees for: {}'.format(record_xpath))

        trees = self.session.get_subtrees(record_xpath)  # type: sr.Trees

        if not trees:
            self.write_line('END')
            return

        for i in range(trees.tree_cnt()):
            rrset = self.get_rrset_from_tree(trees.tree(i))
            self.write_rrset(rrset)

        self.write_line("END")

    def handle_axfr_query(self, domain: str) -> None:
        """
        Retrieves all DNS records for a zone and sends them one by one to PowerDNS

        :param str domain: The name of the zone requested
        """

        if self.get_domain(domain) != domain:
            self.write_line('FAIL')
            return

        record_xpath = '{zone_xpath}[domain="{domain}"]'.format(
                zone_xpath=self.zone_xpath,
                domain=domain)

        tree = self.session.get_subtree(record_xpath)
        rrsets = tree.first_child()

        # Iterate over all nodes underneath the /zone node
        while rrsets:
            if rrsets.name() != 'rrset':
                # ignore everything that is not an rrset node
                rrsets = rrsets.next()
                continue

            rrset = dict()

            # Iterate over all children of the rrset in the tree
            rrset_val = rrsets.first_child()
            while rrset_val:
                if rrset_val.name() in ['ttl']:
                    rrset[rrset_val.name()] = rrset_val.data().get_uint32()
                if rrset_val.name() in ['owner']:
                    rrset[rrset_val.name()] = rrset_val.data().get_string()
                if rrset_val.name() in ['type']:
                    rrset[rrset_val.name()] = rrset_val.data().get_enum()
                if rrset_val.name() in ['rdata']:
                    if not rrset.get(rrset_val.name()):
                        rrset[rrset_val.name()] = list()
                    rrset[rrset_val.name()].append(rrset_val.data().get_string())
                rrset_val = rrset_val.next()

            self.write_rrset(rrset)
            rrsets = rrsets.next()

        self.write_line('END')

def main():
    be = YANGBackend()
    be.run()


if __name__ == "__main__":
    main()
