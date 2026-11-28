# kiksen.netconf.port_reset

Reset a port (shutdown, then no shutdown)

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `port_reset_interface` | str | yes |  | Interface name of the port, e.g. GigabitEthernet1/0/5. |
| `port_reset_delay` | int | no | `3` | Seconds the port stays shut down before it is brought up again. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_reset
  vars:
    port_reset_interface: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_reset`).
