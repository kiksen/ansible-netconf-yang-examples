# kiksen.netconf.port_channel_remove

Port-Channel per NETCONF entfernen

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_channel_remove_interface` | str | yes |  | Name of the port-channel, e.g. Port-channel2. Other interface types are rejected. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_channel_remove
  vars:
    port_channel_remove_interface: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_channel_remove`).
