# Changelog

## 0.1.0

- First release as the collection `kiksen.netconf`.
- Roles are flat now: `netconf/port/access` is `kiksen.netconf.port_access`, and so on.
- Jinja filters (`interface_part`, `rep_segment`, `vlan_list`, `with_native_vlan`, `port_facts`) moved to `plugins/filter/`.
- The NetBox roles moved to the collection `kiksen.netbox`.
