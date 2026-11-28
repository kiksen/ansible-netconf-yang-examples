# kiksen.netconf.port_channel_member

Write a port as port-channel member

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_channel_member_interface` | str | yes |  | Interface name of the physical port, e.g. GigabitEthernet1/0/7. |
| `port_channel_member_number` | int | yes |  | Number of the port-channel (channel-group). |
| `port_channel_member_mode` | str | no | `active` | Channel mode (LACP active/passive or on). |
| `port_channel_member_description` | str | no |  | Interface description. Without a value it is not written. |
| `port_channel_member_service_policy_out` | str | no | `QUEUE-OUT` | Name of the policy-map applied as output service-policy. |
| `port_channel_member_enabled` | bool | no | `True` | Administrative state of the interface; false writes shutdown, true removes it. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_channel_member
  vars:
    port_channel_member_interface: <value>
    port_channel_member_number: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_channel_member`).
