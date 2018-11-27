#!/usr/bin/env python
from __future__ import print_function

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
import pdns_api_client as ac
import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)

ac.configuration.api_key['X-API-Key'] = 'changeme'
api_instance = ac.ZonesApi()

# virtual int sysrepo::Callback::dp_get_items(
#    const char *    xpath,
#    S_Vals_Holder    vals,
#    uint64_t    request_id,
#    const char *    original_xpath,
#    void *    private_ctx
#  )
# https://www.sysrepo.org/static/doc/html/classsysrepo_1_1Callback.html#aad2f1e586510395c8af20ec1dee32ec4
def module_get_cb(xpath, vals, reqid, origxpath, ctx):
    # This function should get all zones + rrs from the auth and put them in the right place in the tree

    log.debug("module_get_cb called with these args: ")
    log.debug("  xpath: {}", xpath)
    log.debug("  vals: {}", vals)  # These should be modified though....
    log.debug("  reqid: {}", reqid)
    log.debug("  origxpath: {}", origxpath)
    log.debug("  ctx: {}", ctx)

    # TODO parse xpath to see what zone we need to fetch

    # TODO do the API call e.g.:
    # zone = api_instance.list_zone('localhost', xpathZone)  # type: ac.Zone
    # log.debug("retrieved zone {} from the API with data {}", xpathZone, zone)
    # serialToReturn = zone.serial
    # recordsToProcess = zone.rrsets
    # zoneType = zone.type
    # etc...

    # TODO allocate a vals large enough (https://www.sysrepo.org/static/doc/html/classsysrepo_1_1Vals__Holder.html)

    # TODO generate sr.Vals and fill it up with sr.Val (?)
    # TODO https://www.sysrepo.org/static/doc/html/classsysrepo_1_1Vals.html
    # TODO https://www.sysrepo.org/static/doc/html/classsysrepo_1_1Val.html

    return sr.SR_ERR_OK


def main():
    try:
        module_name = "dns-server-amended-with-zone"

        log.debug("connecting to sysrepo")
        # connect to sysrepo
        conn = sr.Connection("pdns")
        log.info("connected to sysrepo")

        log.debug("starting session")
        # start session
        sess = sr.Session(conn)
        log.info("session started")

        log.debug("starting subscription")
        # Subscribe to state get events
        subscribe = sr.Subscribe(sess)
        log.info("subscribe successful")

        # void sysrepo::Subscribe::dp_get_items_subscribe   (   const char *    xpath,
        #   S_Callback    callback,
        #   void *    private_ctx = nullptr,
        #   sr_subscr_options_t    opts = SUBSCR_DEFAULT
        # )
        # https://www.sysrepo.org/static/doc/html/classsysrepo_1_1Subscribe.html#af3d53b9e45eb1ed77724c6d4c7a6dffa
        log.debug("registring callbacks")
        subscribe.dp_get_items_subscribe("/" + module_name + ":*//*", module_get_cb)
        log.info("callbacks registered")

        log.warning("starting global_loop")
        sr.global_loop()

        print("Application exit requested, exiting.\n")

    except Exception as e:
        print(e)
        raise  # show me the whole trace


if __name__ == "__main__":
    main()
