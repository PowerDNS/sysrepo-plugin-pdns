#!/usr/bin/env python3

__author__ = "Pieter Lexis <pieter.lexis@powerdns.com"
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

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()


class YANGBackend:
    module_name = 'dns-server-amended-with-zone'
    root_xpath = '/{}:dns-server'.format(module_name)
    zones_xpath = '{}/zones'.format(root_xpath)
    zone_xpath = '{}/zone'.format(zones_xpath)

    def __init__(self):
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

            if qtype in ['SOA', 'ANY']:
                self.get_soa(qname)

            self.write_line("END")

    def write_line(self, line: str):
        log.debug("Sending line to PowerDNS: %s", line)
        sys.stdout.write(line)
        sys.stdout.write('\n')
        sys.stdout.flush()

    def handle_helo(self, line):
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

        self.write_line('OK\tYANG backend ready')

    def get_config_data(self, xpath: str):
        log.debug("Getting config data at '%s'", xpath)

        try:
            values = self.session.get_items(xpath)
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

    def get_soa(self, qname):
        select_xpath = '{}["{}"]/{}/SOA'.format(self.zone_xpath, qname, qname)

        values = self.get_config_data(select_xpath)

        if values is None:
            return

        # self.write_line('DATA\t{}\tIN\tSOA\t{}\t-1\t{}'.format(qname, ))
        return


def main():
    be = YANGBackend()
    be.run()


if __name__ == "__main__":
    main()
