Why NETCONF/YANG
================

Please watch `the video <https://www.youtube.com/watch?v=Vr4kB1_6fLQ>`__ linked on the main page for a good introduction to NETCONF and YANG.

The key take-aways are:

* Each network element is a blackbox to the management application
   * But is described with YANG
   * The device reports its capabilities via NETCONF
* There is a clear separation between operational data (statistics and device state) and configuration data in the models
* The whole system is transaction-based (the set of changes is fully applied, or not at all)
* Ordering the set of changes is the device's job
* This system reduces time and complexity for the operators, at the expense of the vendors

YANG and NETCONF came out of the discussions following :rfc:`3535`, where is was clear that SNMP failed when it came to configuring devices.

.. toctree::
   :maxdepth: 2
   :caption: Further reading:

   NETCONF
   YANG
