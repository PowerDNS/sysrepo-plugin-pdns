NETCONF
=======

NETCONF is a vendor-neutral, IETF :rfc:`standard <6241>` that can be used to configure and query network devices.
The protocol is XML-based. Hence, all data is in a tree-structure by design and supports xpath for sub-tree manipulation.

There is a `helpful video <https://www.youtube.com/watch?v=xoPZO1N-x38>`__ that goes through all the basics.

Some things to remember:

* a **server** is a device that accepts SSH connections for NETCONF
* a **client** is usuall an NMS or other management system that controls the network

NETCONF is carried over SSH and there are no custom authentication, authorization or encryption methods specified.

A NETCONF conversation with a device starts with a ``hello`` message exchange where the device sends its capabilities to the client.
The server can send over the supported YANG models to the client, meaning that no preconfiguration of the client is required.

When configuring a device, the client sends a set of configuration changes and where to apply them.
Many devices support a candidate datastore where this configuration is set and validated before it can be committed to the running datastore using another NETCONF command.
The set of changes should be ordered by the server and applied when requested to do so.
