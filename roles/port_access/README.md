# kiksen.netconf.port_access

Write an access port per NETCONF

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_access_interface` | str | yes |  | Interface name, e.g. GigabitEthernet1/0/5 (Gi1/0/5 works too). |
| `port_access_vlan` | int | yes |  | Access VLAN. |
| `port_access_voice_vlan` | int | no | `None` | Voice VLAN. Without a value an existing voice VLAN is removed. |
| `port_access_description` | str | yes |  | Interface description. |
| `port_access_no_cdp_enable` | bool | no | `None` | Disable CDP on the port (cdp enable = false). With false or without a value the setting is removed. |
| `port_access_no_lldp_transmit` | bool | no | `None` | Disable LLDP transmit (no lldp transmit). With false or without a value the setting is removed. |
| `port_access_no_lldp_receive` | bool | no | `None` | Disable LLDP receive (no lldp receive). With false or without a value the setting is removed. |
| `port_access_service_policy_out` | str | no | `QUEUE-OUT` | Name of the policy-map applied as output service-policy. |
| `port_access_enabled` | bool | no | `True` | Administrative state of the interface; false writes shutdown, true removes it. |
| `port_access_storm_rising` | float | no | `10.0` | Storm-control rising threshold in percent, used for broadcast and multicast. |
| `port_access_storm_falling` | float | no | `0.0` | Storm-control falling threshold in percent, used for broadcast and multicast. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_access
  vars:
    port_access_interface: <value>
    port_access_vlan: <value>
    port_access_description: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_access`).
