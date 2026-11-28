# kiksen.netconf.system_vlan

Write the VLAN list of the device per NETCONF

With the default operation replace, the list replaces the whole native/vlan container (edit-config replace). VLANs that are not in the list are removed, and so is every other setting below native/vlan.

With the operation merge, the listed VLANs are added or updated and nothing is removed. A VLAN without a name keeps its current name.

VLAN 1 is the default VLAN; it cannot be renamed and the device does not store it, so it is accepted in the list but not written. VLANs 1002-1005 are reserved and rejected.

A VLAN name has 1 to 20 characters and must be unique. Allowed are printable ASCII characters without whitespace and without the question mark. The name default is reserved for VLAN 1.

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `system_vlan_operation` | str | no | `replace` | replace swaps the whole VLAN list, merge only adds and updates the listed VLANs. |
| `system_vlan_list` | list | yes |  | VLANs to write, at least one besides VLAN 1. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.system_vlan
  vars:
    system_vlan_list: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.system_vlan`).
