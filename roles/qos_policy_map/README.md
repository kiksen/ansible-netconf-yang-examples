# kiksen.netconf.qos_policy_map

Write class-maps and an egress policy-map per NETCONF

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `qos_policy_map_name` | str | no | `QUEUE-OUT` | Name of the policy-map. |
| `qos_policy_map_classes` | list | no |  | Classes of the policy-map in order. See defaults/main.yml for an example. |

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.qos_policy_map
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.qos_policy_map`).
