# kiksen.netconf.port_channel

Write a port-channel as trunk or access port per NETCONF

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_channel_interface` | str | yes |  | Interface-Name, z.B. Port-channel2. |
| `port_channel_description` | str | yes |  | Interface description. |
| `port_channel_mode` | str | no | `trunk` | Switchport mode of the port-channel. |
| `port_channel_access_vlan` | int | no | `None` | Access VLAN; required, and only allowed, for mode access. |
| `port_channel_allowed_vlans` | raw | no | `None` | Required for mode trunk, not allowed for access. Allowed VLANs: the string all (NetBox tagged-all), a list (e.g. [100, 200, 300]), a range string (e.g. 2-4094 or 1,20-30) or a mixed list (e.g. [1, "20-30", 100]). Valid range 1-4094. |
| `port_channel_native_vlan` | int | no | `None` | Native VLAN (NetBox untagged). Without a value an existing native VLAN is removed. |
| `port_channel_enabled` | bool | no | `True` | Administrative state of the interface; false writes shutdown, true removes it. |
| `port_channel_storm_rising` | float | no | `10.0` | Storm-control rising threshold in percent, used for broadcast and multicast. |
| `port_channel_storm_falling` | float | no | `0.0` | Storm-control falling threshold in percent, used for broadcast and multicast. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_channel
  vars:
    port_channel_interface: <value>
    port_channel_description: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_channel`).
