Design of the plugin
====================

The zone and record management plugin is a python application that listens to traffic from the sysrepo engine and uses the `API <https://doc.powerdns.com/authoritative/http-api/>`__ in the Authoritative Server to enact all the requested changes.

The initial version will be written in Python 3 for rapid prototyping.

Some thoughts about this:

* It would make sense to use the swagger-file from the PowerDNS repo to create the API connector module
* It should do multiple changes in one request, so the transactional nature of NETCONF is kept
