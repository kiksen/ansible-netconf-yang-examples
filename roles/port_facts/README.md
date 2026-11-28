# kiksen.netconf.port_facts

Read all ports and return them grouped by kind

Has one option (below). Always reads all kinds with one get-config.

Return values (set with set_fact):

port_facts_all (list of dict): every interface; fields are listed below.

port_facts_access (list of dict): entries of kind access.

port_facts_trunk (list of dict): entries of kind trunk.

port_facts_member (list of dict): entries of kind member (port-channel members).

port_facts_channel (list of dict): entries of kind channel (Port-channel interfaces).

port_facts_unconfigured (list of dict): entries of kind unconfigured (no switchport mode, no channel-group).

Fields of every entry: interface (str), kind (str), mode (str or null; access, tagged, tagged-all), description (str or null), enabled (bool, false when shut down), untagged_vlan (int or null; the native VLAN on trunks), voice_vlan (int or null), tagged_vlans (list of int or null; without the native VLAN), tagged_vlan_ranges (list of str or null), vlan_has_range (bool), no_cdp_enable (bool), no_lldp_transmit (bool), no_lldp_receive (bool), channel_group (int or null), channel_group_mode (str or null).

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_facts_expand_vlans` | bool | no | `False` | List every tagged VLAN in tagged_vlans. Without it, runs of at least 4 consecutive VLANs are reported as ranges (e.g. 102-200) in tagged_vlan_ranges. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_facts
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_facts`).
