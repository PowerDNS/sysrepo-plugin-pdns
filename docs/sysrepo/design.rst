Design of the plugin
====================

There are two components to this plugin, one is a pipe-backend script for the PowerDNS authoritative that retrieves record data from the sysrepo YANG datastore.
The other part is a service that subsribes to and validates zone-data changes.

This design was chosen because the YANG datastore has all the information required for PowerDNS to serve the records.
Using a database backend would mean using the API to update records.
The problem with this is how to handle changes to the datastore that have been made when the server was not running.
On start-up of the server, the records should then be synced to the database.
With large and/or many zones this can cause issues.

The logical architecture of this design comes down to this::

  [ PowerDNS w/ pipe-yang-backend ]    [ sysrepo-plugin-pdns ]
       ^                                          ^
       | fetches data in response                 | Subscribes to the data model
       | to queries (sysrepo protocol).           | and listens for changes (sysrepo protocol).
       v                                          v
  [                  sysrepo YANG data store                 ]
          ^                                   ^
          | Modifies zone data                | Modifies zone data
          v                                   v
  [ sysrepocfg ]                       [ Netopeer server ] <-----> [ Netopeer client ]
                                                           NETCONF

.. note::
  Why are these components separate? During a first iteration the validator and backend were in one script.
  But as PowerDNS launches more than one process, interesting locking issue could occur in sysrepo.
  Also, the co-process running within the PowerDNS process-space did not seem to like starting threads from Python.

Components
----------
Both components are written in Python 3.6.

``pipe-yang-backend.py``
^^^^^^^^^^^^^^^^^^^^^^^^
This script implements the `pipe-command <https://doc.powerdns.com/authoritative/backends/pipe.html>`__ script.

``sysrepo-plugin-pdns.py``
^^^^^^^^^^^^^^^^^^^^^^^^^^
This service subscribes to the ``/dns-server-amended-with-zone:dns-server`` datastore to

1. Allow sysrepo to change data in the datastore
2. Check the changes before they are committed to the datastore

Having this in a service separate from the pipe-backend script means that data can be modified, even when PowerDNS is not running.

Future Work
-----------
Many things can be done to improve and extend this plugin, a selection:

Rewrite as a remote-backend script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Rewriting as a `remote backend <https://doc.powerdns.com/authoritative/backends/remote.html>`__ plugin that uses pipes to communicate.
This could be used to fold both scripts into one service.

Another advantage would be that thsi backend can then support

* DNSSEC
* Master operation (NOTIFY)
* `Domain metadata <https://doc.powerdns.com/authoritative/domainmetadata.html>`__

The latter (domain metadata) is interesting as things like ``ALSO-NOTIFY`` and ``ALLOW-AXFR`` are already available in dns-server.yang under a part of the model.

Use another language
^^^^^^^^^^^^^^^^^^^^
Rewriting the plugin in something else than Python (perhaps Go or c++) can help with potential performance issues.
Another advantage would be the

Extend to support setting service options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The plugin could look at service options, modify ``pdns.conf`` and control/restart the ``pdns_server`` process, allowing it to revert to the previous version and tell the NETCONF client the transaction failed.
