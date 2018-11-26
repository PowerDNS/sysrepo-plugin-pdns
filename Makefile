check: dns-server-amended-with-zone.yang
	pyang -p .:dns-server-yang:jetconf-knot/yang-modules dns-server-amended-with-zone.yang

.PHONY: check
