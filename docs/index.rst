.. PowerDNS Authoritative Server YANG model and sysrepo plugin documentation master file, created by
   sphinx-quickstart on Mon Nov 26 10:53:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PowerDNS Authoritative Server YANG model and sysrepo plugin's documentation!
=======================================================================================

This documentation serves as the documentation for the YANG model(s), the sysrepo plugin and as a YANG and NETCONF reference.

What's all this about?
----------------------

In the networking world there's a push towards a vendor independent, pluggable way of configuring the whole network.
The `IETF <https://ietf.org>`__ has standardized :rfc:`YANG <6020>` and :rfc:`NETCONF <4741>` to enable this.

:doc:`YANG <intro/YANG>` is the data-modeling language that allows for specifying protocol and device features whereas :doc:`NETCONF <intro/NETCONF>` is the protocol used to set and retrieve configuration and operational data form devices.
`This <https://www.youtube.com/watch?v=Vr4kB1_6fLQ>`__ video from `Tail-f systems <http://www.tail-f.com/>`__ provides a short overview of and backgrounds on these technologies.

`sysrepo <http://sysrepo.org/>`__ is YANG datastore that allows UNIX programs to be configured using NETCONF/YANG.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   intro/why
   models/intro
   sysrepo/intro
   setting-up/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
