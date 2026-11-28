# kiksen.netconf

Ansible collection with roles and Jinja filters that configure Cisco IOS-XE switches
via NETCONF-YANG (`Cisco-IOS-XE-native` model).

The IOS resource modules using SSH are still more powerful, but with NETCONF it is quite easy to build those roles,
since NETCONF brings features like replacing or removing configuration without any extra programming or checking work.
NETCONF is also much faster than the IOS resource modules.

## Switch configuration

NETCONF must be enabled on the switch, and the Ansible user needs privilege 15:

```text
aaa new-model
aaa authentication login default local
aaa authorization exec default local
username <user> privilege 15 secret <password>
!
netconf-yang
```

NETCONF listens on TCP port 830 by default. Check it with `show netconf-yang status`.
Point the inventory at it (see `examples/inventory.yaml`):

```yaml
ansible_connection: ansible.netcommon.netconf
ansible_network_os: cisco.ios.ios
ansible_port: 830
```

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

## Content - Port roles

These roles push one complete interface configuration to the device. This means you can change it entirely without losing
connectivity. Change the templates if you want another configuration.

| Role | Purpose |
| --- | --- |
| `kiksen.netconf.port_access` | Write an access port (replace, so the port equals the template, no old configuration remains) |
| `kiksen.netconf.port_trunk` | Write a physical port as trunk (replace), no old configuration remains |
| `kiksen.netconf.port_channel` | Write a port-channel as trunk or access port (replace) |
| `kiksen.netconf.port_channel_member` | Make a physical port a port-channel member |
| `kiksen.netconf.port_channel_remove` | Remove a port-channel |
| `kiksen.netconf.port_shutdown` | Shut down a port without touching its other settings |
| `kiksen.netconf.port_reset` | Reset a port (shutdown, wait, no shutdown), e.g. to renew a DHCP lease |

## Content - Port facts

| Role | Purpose |
| --- | --- |
| `kiksen.netconf.port_facts` | Read all ports, grouped by kind of port. Useful to write existing device data to NetBox or other systems, or to rewrite the existing configuration with exactly the configuration from the Jinja templates defined here. |
| `kiksen.netconf.port_channel_facts` | Read all port-channels as a list |

The `*_facts` roles return their data in `<role>_*` variables.

## Content - System facts

| Role | Purpose |
| --- | --- |
| `kiksen.netconf.system_facts` | Read the output of show version, show inventory, the stack information and the active VLANs |
| `kiksen.netconf.neighbor_facts` | Read the CDP and LLDP neighbors |

## Content - System / Global configuration

| Role | Purpose |
| --- | --- |
| `kiksen.netconf.system_vlan` | Write the VLAN list of the device (replace or merge) |
| `kiksen.netconf.system_hostname` | Write the hostname of the device |
| `kiksen.netconf.qos_policy_map` | Write class-maps and an egress policy-map |
| `kiksen.netconf.write_mem` | Handler `netconf save config` (write memory), no parameters |

Every role has its own `README.md` in `roles/<name>/` and a `meta/argument_specs.yml`
(`ansible-doc -t role kiksen.netconf.port_access`) with parameters and return values.

### Filters

Always use the FQCN; short names do not resolve inside roles.

| Filter | Example | Result |
| --- | --- | --- |
| `kiksen.netconf.interface_part` | `'Gi1/0/5' \| kiksen.netconf.interface_part('type')` | `GigabitEthernet` |
| `kiksen.netconf.vlan_list` | `[1, 20, 21, 22] \| kiksen.netconf.vlan_list` | `1,20-22` |
| `kiksen.netconf.with_native_vlan` | `[100, 200] \| kiksen.netconf.with_native_vlan(10)` | `[100, 200, 10]` (`all` stays `all`) |
| `kiksen.netconf.rep_segment` | `'Gi1/0/1' \| kiksen.netconf.rep_segment` | REP segment of a port |
| `kiksen.netconf.port_facts` | `xml \| kiksen.netconf.port_facts(expand=false)` | list of port facts |

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

More playbooks and a lab inventory are in
[`examples/`](https://github.com/kiksen/ansible-collection-netconf/tree/main/examples)
(not part of the built collection), e.g. `access_port.yaml`, `trunk_port.yaml`,
`trunk_channel.yaml`, `netconf_rewrite.yaml` and the facts playbooks.

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

## Release and upload to Galaxy

A release is published to Galaxy by GitHub Actions (`.github/workflows/release.yml`) when a tag `vX.Y.Z` is pushed.
Normal pushes and pull requests only run the tests (`ci.yml`) and never upload.

One-time setup:

1. Log in at <https://galaxy.ansible.com> with GitHub (the namespace `kiksen` is created automatically).
2. Create an API token there (*Collections -> API token*).
3. Add it to the GitHub repository as the secret `GALAXY_API_KEY`
   (*Settings -> Secrets and variables -> Actions -> New repository secret*).

For every release:

1. Raise `version` in `galaxy.yml` (semantic versioning) and describe the change in `CHANGELOG.md`.
2. Check locally: `uv run ruff check && uv run pytest && uv run ansible-lint`.
3. Optional: build the package and look at its content: `uv run ansible-galaxy collection build` and `tar tzf kiksen-netconf-0.1.0.tar.gz`.
4. Commit and push to `main`, wait until the `CI` workflow is green.
5. Tag and push the tag (the tag must match `version` in `galaxy.yml`, otherwise the release fails):

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

6. Watch the run under *Actions -> Release*. On success the collection is on Galaxy and a GitHub release with the tarball exists.

Notes:

- A published version cannot be overwritten. Fix an error with the next patch version.
- If the release run fails before the publish step, delete the tag (`git push --delete origin v0.1.0`, `git tag -d v0.1.0`), fix the problem and tag again.
- Manual upload without GitHub: `uv run ansible-galaxy collection publish kiksen-netconf-0.1.0.tar.gz --token <token>`.
