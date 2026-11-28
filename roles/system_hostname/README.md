# kiksen.netconf.system_hostname

Write the hostname of the device per NETCONF

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `system_hostname_name` | str | yes |  | New hostname of the device, e.g. sw-access-01. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.system_hostname
  vars:
    system_hostname_name: <value>
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.system_hostname`).
