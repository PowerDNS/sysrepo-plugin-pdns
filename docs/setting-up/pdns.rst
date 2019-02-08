Setting up PowerDNS and the Pipe-backend
========================================

PowerDNS Authoritative Server can be installed either from the OS software repositories or from `the PowerDNS repositories <https://repo.powerdns.com>`__.
Both the main server package (``pdns-server``) and the Pipe-backend package (``pdns-backend-pipe``) must be installed and be of version 4.1.0 or higher.

After installing, the pipe backend needs to be configured, add the following to ``/etc/powerdns/pdns.conf`` (or the equivalent for the OS in use)::

  launch=pipe
  pipe-abi-version=4
  pipe-command=/var/lib/powerdns/pipe-yang-backend.py

Then restart the PowerDNS service (``systemctl restart pdns.service``).
