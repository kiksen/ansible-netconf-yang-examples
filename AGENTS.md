# AGENTS.md - Ansible NETCONF roles

## Toolchain
- Use **uv**: `uv sync`, `uv run ansible-playbook -i examples/inventory.yaml examples/<playbook>.yaml`. Never call a globally installed `ansible-playbook`; it lacks `ncclient`.
- Lint with `uv run ansible-lint`. Run `uv run ruff check` and `uv run pytest` for the Python filter plugins.

## Layout
- This repo is the Ansible collection `kiksen.netconf`. Roles are flat: `roles/<area>_<object>/`, e.g. `roles/port_access`. Reference them with the FQCN: `role: kiksen.netconf.port_access`.
- Playbooks and the lab inventory live in `examples/` and are not part of the built collection (`build_ignore` in `galaxy.yml`). NetBox roles live in the collection `kiksen.netbox` (own repo).
- Every role has `meta/main.yml`, `meta/argument_specs.yml`, `defaults/main.yml`, `tasks/main.yml` and a Jinja template in `templates/`.
- Example XML (output of `read_interface.yaml -e dump=<name>`) goes in `xml_example/`. Build templates from these files.
- Jinja filters live in `plugins/filter/`. Always use the FQCN in roles and playbooks (`| kiksen.netconf.vlan_list`); short names do not resolve.

## Variable naming
- **Every** variable defined by a role starts with the role name: `roles/port_access` -> `port_access_`.
  - Parameters: `port_access_interface`, `port_access_vlan`, `port_access_voice_vlan`, `port_access_description`.
  - Registered results: `port_access_<what>_result`, e.g. `port_access_edit_result`.
  - Variables set with `set_fact` or `{% set %}` in templates: `port_access_<what>`.
- After the prefix use a short, descriptive snake_case noun. Never use generic names like `result`, `data`, `vlan`, `tmp`.
- Optional parameters default to `null` in `defaults/main.yml`. Required parameters have no default and are marked `required: true` in `argument_specs.yml`.
- Playbooks pass role parameters under their prefixed names; do not rename them in playbooks.
- Task names are English; a Jinja expression may only appear at the end of a name (`name[template]`).

## NETCONF conventions
- Use `ansible.netcommon.netconf_get` to read and `ansible.netcommon.netconf_config` to write.
- Use the `Cisco-IOS-XE-native` model. The `ietf-interfaces` model lacks VLAN, spanning-tree and storm-control.
- `netconf_config` content must have `<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">` as root.
- Use `merge`. To clear an optional setting, put `nc:operation="remove"` on that element instead of omitting it.
- Parse interface names with the `interface_part` filter (`type`, `switch`, `slot`, `subslot`, `port`, `id`). Do not split strings in templates.

## Workflow
- Before finishing: `uv run ansible-lint`, `uv run ruff check`, `uv run pytest` must pass.
- A re-run with unchanged values must report `changed=0` where the module allows it.
- Never commit credentials. The lab inventory uses test credentials only.

## YAML formatting
- Indent YAML in steps of 2 spaces only. Continuation lines of folded (`>-`) or literal scalars use the indent of the first line plus a multiple of 2; do not align them under an opening bracket. VS Code (indent-rainbow) marks odd indents red.

## Language
- create all comments and documentation in english

## Python test client
- This client is only for testing and exploring things manually. General changes are not done to python unless you are instructued to.

## Yang Models
- find all Cisco Yang Models in ./yanmodels as a reference. 