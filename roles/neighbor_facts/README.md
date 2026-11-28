# kiksen.netconf.neighbor_facts

Read the CDP and LLDP neighbors

Has no parameters.

Return values (set with set_fact):

neighbor_facts_cdp (list of dict): one dict per CDP neighbor (device-name, local-intf-name, port-id, platform-name, capability, ...), read from Cisco-IOS-XE-cdp-oper.

neighbor_facts_lldp (list of dict): one dict per LLDP neighbor (device-id, local-interface, connecting-interface, ttl, ...), read from Cisco-IOS-XE-lldp-oper.

Both lists are empty when the device has no neighbors.

## Example

```yaml
- ansible.builtin.include_role:
    name: kiksen.netconf.neighbor_facts
```

The full specification is in `meta/argument_specs.yml` (`ansible-doc -t role kiksen.netconf.neighbor_facts`).
