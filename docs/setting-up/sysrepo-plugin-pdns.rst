Setting up the subscription service
===================================
After installing the ``sysrepo-plugin-pdns.py`` script into ``/usr/local/bin``, it will need to be started.
Create the ``/etc/systemd/system/sysrepo-plugin-pdns.service`` with this content:

.. literalinclude:: ../../systemd/sysrepo-plugin-pdns.service

Then start the service::

  systemctl daemon-reload
  systemctl start sysrepo-plugin-pdns.service
