Requirements
============

The YANG backend is implemented in Python 3.6 and thus requires an installation of Python 3.6 or higher.
There is only one required Python package, which is the sysrepo library for Python 3.

Building this library can be done by installing the Python development packages (``libpython3-dev`` on Ubuntu 18.04) and passing ``-DGEN_PYTHON_BINDINGS=true -DGEN_PYTHON_VERSION=3`` to the call to ``cmake`` when configuring sysrepo.

Furthermore, this plugin requires PowerDNS Authoritative Server 4.1 or higher.
