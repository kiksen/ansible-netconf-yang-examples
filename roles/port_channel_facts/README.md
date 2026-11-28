# kiksen.netconf.port_channel_facts

Read all port-channels of the switch as a list

port_channel_facts_list (list of str): all port-channels, e.g. Port-channel1, Port-channel2.

The list is sorted by number.

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.port_channel_facts
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.port_channel_facts`).
