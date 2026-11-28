# kiksen.netconf.port_shutdown

Shut down a port

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_shutdown_interface` | str | yes |  | Interface name of the port, e.g. GigabitEthernet1/1/1. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_shutdown
  vars:
    port_shutdown_interface: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_shutdown`).
