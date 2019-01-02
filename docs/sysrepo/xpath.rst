XPath Queries and Data Model
============================

When using the sysrepo client library, queries against the data store are performed using XPath queries against the XML representation of the data.

Here is an example XML representation of a server configuration with one zone defined for ``example.com``::

  <dns-server xmlns="http://www.nic.cz/ns/yang/dns-server-amended-with-zone">
    <zones>
      <zone>
        <domain>example.com</domain>
        <rrset>
          <owner>example.com</owner>
          <type>SOA</type>
          <ttl>3600</ttl>
          <rdata>localhost. hostmaster.localhost. 20181217 3600 1800 604800 600</rdata>
        </rrset>
        <rrset>
          <owner>example.com</owner>
          <type>A</type>
          <ttl>3600</ttl>
          <rdata>1.2.3.4</rdata>
          <rdata>42.42.42.42</rdata>
        </rrset>
      </zone>
      <zone>
        <domain>what.com</domain>
      </zone>
    </zones>
  </dns-server>

For example, when receiving a query for A records of ``example.com``. This will result in an XPath query to the datastore that looks like this::

  /dns-server-amended-with-zone:dns-server/zones/zone[domain="example.com"]/rrset[type="A"]/rdata[text()]

Let's break that down.

 * ``/dns-server-amended-with-zone:dns-server``

   This matches our root ``dns-server`` element. Note that sysrepo internally seems to just use the shortened "dns-server-amended-with-zone" rather than the fully qualified URI for the namespace. Hence, testing XPath queries with other tools may require omitting the namespace.

 * ``/zones``
 * ``/zone[domain="example.com"]``

   This matches a ``zone`` element with a child ``domain`` element consisting of the text "example.com". Even though we need to check the ``domain`` child, we need the parent ``zone`` element for another child.

 * ``/rrset[type="A"]``

   We need to match the ``rrset`` element which has a child ``type`` element matching our requested record type (here "A", but could be "MX" or "SOA", etc).

 * ``/rdata[text()]``

   This retrieves a list of the text of all the ``rdata`` children of our requested ``rrset``. The ``rdata`` elements contain the responses to the query, returned to PowerDNS as separate responses.
