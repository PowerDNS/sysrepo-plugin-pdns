#!/usr/bin/env python3
__author__ = "Pieter Lexis <pieter.lexis@powerdns.com>"
__copyright__ = "Copyright 2018-2019, PowerDNS.COM BV"
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

import re
import sys
import sysrepo as sr
import logging
import requests

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()


base_url = 'http://127.0.0.1:8081/api/v1/servers/localhost/'
api_key = 'blabla'


def change_cb(session: sr.Session, modname: str, event, ctx) -> int:
    log.debug("change_cb called with:")
    log.debug("  session: %s", session)
    log.debug("  modname: %s", modname)
    log.debug("  event: %s", event)
    log.debug("  ctx: %s", ctx)

    try:
        change_iter = session.get_changes_iter("/cznic-dns-slave-server:dns-server/zones")
        change = session.get_change_next(change_iter)

        while change:
            log.debug("Change")
            log.debug("  type: %i", change.oper())
            old: sr.Val = change.old_val()
            if old:
                log.debug("  old: %s", old.to_string())
                m = re.search(r"(^.*/zones/zone\[domain=\'([^']*)'\])", old.to_string())

            new: sr.Val = change.new_val()
            if new:
                log.debug("  new: %s", new.to_string())
                m = re.search(r"(^.*/zones/zone\[domain=\'([^']*)'\])", new.to_string())

            if not m:
                change = session.get_change_next(change_iter)
                continue

            xpath = m.group(1)
            log.debug("  xpath: %s", xpath)
            name = m.group(2)
            log.debug("  name: %s", name)

            # Get the addresses for all masters
            addr: sr.Vals = session.get_items(xpath + '/master')
            addrs = list()
            if addr:
                log.debug('Masters:')
                for addr_iter in range(addr.val_cnt()):
                    log.debug('  name: %s', addr.val(addr_iter).val_to_string())
                    remote: sr.Val = session.get_item("/cznic-dns-slave-server:dns-server/remote-server[name='{}']/remote/ip-address".format(
                        addr.val(addr_iter).val_to_string()))
                    if remote:
                        log.debug('    address: %s', remote.val_to_string())
                        addrs.append(remote.val_to_string())
            log.debug("New master addresses for %s: %s", name, ', '.join(addrs))

            resp = requests.get(base_url + '/zones?zone={zone}.'.format(zone=name),
                                headers={'X-Api-Key': api_key, 'Accept': 'application/json'})
            ans = resp.json()

            # The request we're going to send out to the auth
            req = requests.Request('POST',
                                   base_url + '/zones',
                                   headers={'X-Api-Key': api_key, 'Accept': 'application/json'})
            if len(ans):
                # zone exists
                req.method = 'PUT'
                req.url = 'http://127.0.0.1:8081' + ans[0]['url']

            req.json = {
                "name": name + '.',
                "kind": 'Slave',
                "masters": addrs,
            }

            resp = requests.session().send(req.prepare())

            change = session.get_change_next(change_iter)

    except Exception as ex:
        log.warning(ex)
        log.debug(ex.with_traceback())
        return sr.SR_ERR_OPERATION_FAILED

    return sr.SR_ERR_OK


def main():
    log.debug("connecting to sysrepo")

    # connect to sysrepo
    conn = sr.Connection("pdns-configurator")
    log.info("connected to sysrepo")

    log.debug("starting session")

    # start session
    session = sr.Session(conn)
    log.info("session started")
    sub = sr.Subscribe(session)

    # module_change_subscribe API docs:
    #   https://www.sysrepo.org/static/doc/html/group__cl.html#ga35341cf4bf9584127f7c5a79405a878f
    try:
        sub.module_change_subscribe('cznic-dns-slave-server', change_cb,
                                    '/cznic-dns-slave-server:dns-server/zones',
                                    sr.SR_SUBSCR_DEFAULT | sr.SR_SUBSCR_APPLY_ONLY)
    except Exception as ex:
        log.error('unable to subscribe: %s', ex)
        sys.exit(1)

    sr.global_loop()


if __name__ == '__main__':
    main()
