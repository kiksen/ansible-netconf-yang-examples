# kiksen.netconf.port_trunk

Write a physical port as trunk per NETCONF

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_trunk_interface` | str | yes |  | Interface-Name, z.B. GigabitEthernet1/0/6. |
| `port_trunk_description` | str | yes |  | Interface description. |
| `port_trunk_allowed_vlans` | raw | yes |  | Allowed VLANs: the string all (NetBox tagged-all), a list (e.g. [100, 200, 300]), a range string (e.g. 2-4094 or 1,20-30) or a mixed list (e.g. [1, "20-30", 100]). Valid range 1-4094. |
| `port_trunk_native_vlan` | int | no | `None` | Native VLAN (NetBox untagged). Without a value an existing native VLAN is removed. |
| `port_trunk_no_cdp_enable` | bool | no | `None` | Disable CDP on the port (cdp enable = false). With false or without a value the setting is removed. |
| `port_trunk_no_lldp_transmit` | bool | no | `None` | Disable LLDP transmit (no lldp transmit). With false or without a value the setting is removed. |
| `port_trunk_no_lldp_receive` | bool | no | `None` | Disable LLDP receive (no lldp receive). With false or without a value the setting is removed. |
| `port_trunk_rep` | bool | no | `None` | Write the REP segment. Everything is derived from the interface: segment ID = port number (1/0/5 -> 5); switch 1 = edge no-neighbor primary (active Flexlink+ port), switch 2 = edge no-neighbor preferred (standby); other switch numbers are an error. With false or without a value REP is removed. |
| `port_trunk_nonegotiate` | bool | no | `None` | Configure 'switchport nonegotiate' on the port. With false or without a value the setting is removed. |
| `port_trunk_service_policy_out` | str | no | `QUEUE-OUT` | Name of the policy-map applied as output service-policy. |
| `port_trunk_enabled` | bool | no | `True` | Administrative state of the interface; false writes shutdown, true removes it. |
| `port_trunk_storm_rising` | float | no | `10.0` | Storm-control rising threshold in percent, used for broadcast and multicast. |
| `port_trunk_storm_falling` | float | no | `0.0` | Storm-control falling threshold in percent, used for broadcast and multicast. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_trunk
  vars:
    port_trunk_interface: <value>
    port_trunk_description: <value>
    port_trunk_allowed_vlans: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_trunk`).
