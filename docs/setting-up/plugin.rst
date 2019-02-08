Installing the plugin
=====================

As described in :doc:`../sysrepo/design`, this plugin consists of 2 parts, the subscription service and the Pipe-backend script.
Both these scripts are located in the ``pdns/`` directory of the repository.

It is recommended to copy the ``pipe-yang-backend.py`` script to ``/var/lib/powerdns`` and ``sysrepo-plugin-pdns.py`` to ``/usr/local/bin``.
Both scripts will need execute permissions (``chmod +x``).
