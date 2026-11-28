# kiksen.netconf

Ansible collection with roles and Jinja filters that configure Cisco IOS-XE switches
per NETCONF (`Cisco-IOS-XE-native` model).

## Install

```yaml
# requirements.yml
collections:
  - name: https://github.com/kiksen/ansible-collection-netconf.git
    type: git
    version: v0.1.0
```

```bash
ansible-galaxy collection install -r requirements.yml
```

The controller needs the Python package `ncclient` (plus `lxml` for the `port_facts` filter).

## Content

| Role | Purpose |
| --- | --- |
| `kiksen.netconf.port_access` / `port_trunk` / `port_channel` / `port_channel_member` | Write ports (replace, so the port equals the template) |
| `kiksen.netconf.port_shutdown` / `port_reset` / `port_channel_remove` | Shut down, reset, remove |
| `kiksen.netconf.port_facts` / `port_channel_facts` / `neighbor_facts` / `system_facts` | Read data into `<role>_*` variables |
| `kiksen.netconf.system_vlan` / `system_hostname` / `qos_policy_map` | System settings |
| `kiksen.netconf.write_mem` | Handler `netconf save config` (write memory) |

Filters: `interface_part`, `rep_segment`, `vlan_list`, `with_native_vlan`, `port_facts`
(use the FQCN, e.g. `{{ 'Gi1/0/5' | kiksen.netconf.interface_part('type') }}`).
Parameters and return values of every role are in its `meta/argument_specs.yml`.

## Example

```yaml
- hosts: switch
  gather_facts: false
  roles:
    - role: kiksen.netconf.port_access
      vars:
        port_access_interface: GigabitEthernet1/0/5
        port_access_vlan: 10
```

More playbooks and a lab inventory are in `examples/` (not part of the built collection).

## Development

```bash
uv sync
# let Ansible find the working copy as a collection
mkdir -p ~/.ansible/collections/ansible_collections/kiksen
ln -sfn "$PWD" ~/.ansible/collections/ansible_collections/kiksen/netconf
uv run ansible-playbook -i examples/inventory.yaml examples/access_port.yaml
uv run ruff check && uv run pytest && uv run ansible-lint
ansible-galaxy collection build
```

Related collection: `kiksen.netbox` (reads NetBox and calls these roles).
