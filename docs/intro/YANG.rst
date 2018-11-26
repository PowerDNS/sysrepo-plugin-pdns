YANG
====
YANG is described in its :rfc:`RFC <6020>` as follows:

  YANG is a data modeling language used to model configuration and
  state data manipulated by the Network Configuration Protocol
  (NETCONF), NETCONF remote procedure calls, and NETCONF notifications.
  YANG is used to model the operations and content layers of NETCONF.

`This video <https://www.youtube.com/watch?v=33VBb6N4yOY>`__ has a good overview of YANG.

It is a DSL for blackbox representation of a network device, independent of the actual implementation in the device.
YANG is comparable to a more extensible and user-friendly form of the MIBs from the SNMP world.

YANG models are split up into modules and the language supports namespacing, importing and including of modules.

.. todo:: Write about module layout, types, groupings, containers, lists
