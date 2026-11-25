# Port facts: output contract for a second implementation (classic IOS / CLI)

This guide is for an agent that builds a **second reader** for older IOS devices
that have no NETCONF. The output must be **identical** to the output of the role
`netconf/port/facts` (IOS-XE, NETCONF), so that downstream code (NetBox sync,
reports) does not care where the data came from.

Scope: the input is **already parsed** (TextFSM records that contain all the
information listed in section 3). This guide does **not** cover parsing the
device output. It only defines how the parsed information maps to the result
(sections 1 to 5) and how to verify it (section 7).

Reference implementation: `roles/netconf/port/facts/filter_plugins/port_facts.py`
(filter `port_facts`) and its tests `tests/test_port_facts.py`. Reference input
and output: `xml_example/all_interfaces.xml`.

## 1. Result shape

One list. Each entry is one interface, a dict with **exactly these 14 keys**
(all keys always present, never omitted):

| key | type | meaning |
|---|---|---|
| `interface` | str | full interface name, e.g. `GigabitEthernet1/0/2`, `Port-channel30` (no abbreviation, no space) |
| `kind` | str | `access`, `trunk`, `member`, `channel` or `unconfigured` |
| `mode` | str or null | `access`, `tagged`, `tagged-all` (NetBox names) or null |
| `description` | str or null | text of the `description` line, stripped |
| `untagged_vlan` | int or null | access VLAN (access) or native VLAN (trunk) |
| `voice_vlan` | int or null | voice VLAN |
| `tagged_vlans` | list[int] or null | single tagged VLANs, ascending |
| `tagged_vlan_ranges` | list[str] or null | ranges as `"102-200"` |
| `vlan_has_range` | bool | `tagged_vlan_ranges` is not empty |
| `no_cdp_enable` | bool | CDP is disabled on the port |
| `no_lldp_transmit` | bool | LLDP transmit is disabled on the port |
| `no_lldp_receive` | bool | LLDP receive is disabled on the port |
| `channel_group` | int or null | channel-group number |
| `channel_group_mode` | str or null | `active`, `passive`, `on`, `auto`, `desirable` as configured |

Types matter: VLAN IDs and `channel_group` are **integers**, the three `no_*`
flags and `vlan_has_range` are **real booleans**, absent values are `null`
(never `""`, `0` or `false` for a missing number/string).

Example (this is the target format):

```json
{
  "channel_group": null,
  "channel_group_mode": null,
  "description": null,
  "interface": "Port-channel30",
  "kind": "channel",
  "mode": "access",
  "no_cdp_enable": false,
  "no_lldp_receive": false,
  "no_lldp_transmit": false,
  "tagged_vlan_ranges": null,
  "tagged_vlans": null,
  "untagged_vlan": 123,
  "vlan_has_range": false,
  "voice_vlan": null
}
```

## 2. Which interfaces are listed

- Every interface in the running config **except**: types `Vlan`, `Loopback`,
  `Tunnel`, `Null`, `BDI`, and every sub-interface (name contains `.`).
- Include interfaces that have no config lines at all (they become
  `unconfigured`). Do not special-case management or stack ports.
- Order is not significant, but keep it stable (device order is fine).

## 3. Information needed per interface

For every interface the parsed input must provide the following information.
The right-hand column names the IOS config line it comes from, only so you can
recognise the meaning; map it to the field names of the TextFSM records you
get. "Not configured" means the line is absent on the device.

| field | information / IOS config line |
|---|---|
| `description` | `description <text>` (stripped) |
| switchport mode (internal) | `switchport mode trunk|access`, plus presence of trunk/access lines (rule 4.1) |
| `untagged_vlan` | access: `switchport access vlan N`. trunk: `switchport trunk native vlan N` |
| `voice_vlan` | `switchport voice vlan N` (read it regardless of mode; null if absent) |
| tagged VLANs (internal) | all `switchport trunk allowed vlan ...` lines (rule 4.4) |
| `no_cdp_enable` | `no cdp enable` is present |
| `no_lldp_transmit` | `no lldp transmit` is present |
| `no_lldp_receive` | `no lldp receive` is present |
| `channel_group` | N of `channel-group N mode <m>` |
| `channel_group_mode` | `<m>` of that line |

Everything else on the interface is ignored. A default value that the device
does not print is `null`/`false`: do **not** invent defaults (e.g. native VLAN
1, CDP on).

## 4. Rules

### 4.1 Switchport mode (internal value `access` / `trunk` / none)
1. `switchport mode trunk` -> `trunk`; `switchport mode access` -> `access`.
2. Otherwise infer: any `switchport trunk ...` line -> `trunk`; else any
   `switchport access vlan` line -> `access`.
3. Otherwise none. This also covers `switchport mode dynamic ...`,
   `dot1q-tunnel` and `private-vlan`, as long as no trunk/access line exists.

### 4.2 `kind` (first match wins)
1. interface type is `Port-channel` -> `channel`
2. has `channel-group` -> `member` (even if it has trunk/access lines)
3. switchport mode `trunk` -> `trunk`
4. switchport mode `access` -> `access`
5. else `unconfigured`

### 4.3 `mode`, `untagged_vlan`
| switchport mode | `mode` | `untagged_vlan` |
|---|---|---|
| access | `access` | access VLAN or null |
| trunk | `tagged` or `tagged-all` (rule 4.4) | native VLAN or null |
| none | null | null |

`mode` depends only on the switchport mode, not on `kind`. A `member` or
`channel` with trunk lines therefore has `mode` `tagged`; a port-channel without
switchport lines has `mode` null.

### 4.4 Tagged VLANs (trunk only; otherwise `tagged_vlans`, `tagged_vlan_ranges` are null)
Evaluate the `switchport trunk allowed vlan` lines of the block:
- **No such line** -> `mode = tagged-all`, `tagged_vlans = null`,
  `tagged_vlan_ranges = null`.
- `... allowed vlan all` -> same as no line (`tagged-all`).
- `... allowed vlan none` -> `mode = tagged`, empty lists (`[]` and `[]`).
- `... allowed vlan except 10,20` -> `tagged`, all VLANs 1-4094 minus the listed.
- `... allowed vlan 5,100-200` plus any number of `... allowed vlan add 300`
  lines -> `tagged`, the **union** of all listed VLANs.

Then, for `tagged` only:
1. Expand to a set of integers (`5,100-102` -> 5,100,101,102). IDs outside
   1-4094 are an error.
2. **Remove the native VLAN** (`untagged_vlan`) from the set.
3. Sort ascending.
4. Split into singles and ranges: a run of **at least 4 consecutive** VLANs
   becomes a range string `"low-high"`, a shorter run stays as single
   integers. `tagged_vlans` = the singles, `tagged_vlan_ranges` = the ranges,
   both ascending. Both lists are always lists (possibly empty) in `tagged`
   mode.
5. `vlan_has_range = tagged_vlan_ranges is not empty`.

Example: allowed `5,100-200,204,205`, native 101 -> set without 101 ->
`tagged_vlans [5, 100, 204, 205]`, `tagged_vlan_ranges ["102-200"]`,
`vlan_has_range true`. (100 is a run of length 1, 102-200 a run of 99.)

Optional switch `expand` (default false): when true, put **all** VLANs into
`tagged_vlans`, `tagged_vlan_ranges = []`, `vlan_has_range = false` (still null
for access and `tagged-all`).

### 4.5 Flags
`no_*` are false unless the matching `no ...` line exists. They never become
null.

### 4.6 Summary: how each `kind` fills the fields

`kind` only classifies the port (rule 4.2). The VLAN fields always follow the
switchport mode of the interface itself (rules 4.1 to 4.4), whatever the `kind`.
Fields that apply to every kind: `interface`, `description` (null if no line),
`no_cdp_enable`, `no_lldp_transmit`, `no_lldp_receive` (false unless the `no ...`
line exists).

| field | `access` | `trunk` | `member` | `channel` | `unconfigured` |
|---|---|---|---|---|---|
| `mode` | `access` | `tagged` or `tagged-all` | from its own switchport lines, else null | from its own switchport lines, else null | null |
| `untagged_vlan` | access VLAN or null | native VLAN or null | as access/trunk by its own mode, else null | as access/trunk by its own mode, else null | null |
| `voice_vlan` | voice VLAN or null | voice VLAN or null (normally null) | voice VLAN or null | voice VLAN or null | null |
| `tagged_vlans` | null | list of single VLANs (`tagged`), null (`tagged-all`) | like trunk if its mode is trunk, else null | like trunk if its mode is trunk, else null | null |
| `tagged_vlan_ranges` | null | list of ranges, `[]` if none (`tagged`), null (`tagged-all`) | like trunk if its mode is trunk, else null | like trunk if its mode is trunk, else null | null |
| `vlan_has_range` | false | true if ranges not empty | like trunk | like trunk | false |
| `channel_group` | null | null | N | null | null |
| `channel_group_mode` | null | null | mode of the line | null | null |

Notes:
- `member` and `channel` have no VLAN rules of their own. Apply 4.1 to 4.4 to
  their own lines. Typical results: a member without switchport lines has
  `mode` null; a port-channel with `switchport trunk ...` has `mode` `tagged`
  or `tagged-all`; a port-channel with only `switchport access vlan N` has
  `mode` `access`.
- `unconfigured` has no switchport mode and no channel-group, but may still
  carry `description` and the `no_*` flags if those lines exist.

## 5. Complete examples

The config blocks only illustrate which information goes in; the real input
are your TextFSM records.

Access port with voice VLAN and CDP/LLDP disabled:
```
interface GigabitEthernet1/0/5
 description Clients
 switchport access vlan 123
 switchport mode access
 switchport voice vlan 500
 no cdp enable
 no lldp transmit
 no lldp receive
```
```json
{"interface": "GigabitEthernet1/0/5", "kind": "access", "mode": "access",
 "description": "Clients", "untagged_vlan": 123, "voice_vlan": 500,
 "tagged_vlans": null, "tagged_vlan_ranges": null, "vlan_has_range": false,
 "no_cdp_enable": true, "no_lldp_transmit": true, "no_lldp_receive": true,
 "channel_group": null, "channel_group_mode": null}
```

Trunk with list and native VLAN:
```
interface GigabitEthernet1/0/6
 description Uplink
 switchport trunk native vlan 100
 switchport trunk allowed vlan 100,200,300
 switchport mode trunk
```
```json
{"interface": "GigabitEthernet1/0/6", "kind": "trunk", "mode": "tagged",
 "description": "Uplink", "untagged_vlan": 100, "voice_vlan": null,
 "tagged_vlans": [200, 300], "tagged_vlan_ranges": [], "vlan_has_range": false,
 "no_cdp_enable": false, "no_lldp_transmit": false, "no_lldp_receive": false,
 "channel_group": null, "channel_group_mode": null}
```

Trunk without allowed line (all VLANs):
```
interface GigabitEthernet1/0/8
 description TrunkAll
 switchport trunk native vlan 1
 switchport mode trunk
```
-> `kind trunk`, `mode tagged-all`, `untagged_vlan 1`, `tagged_vlans null`,
`tagged_vlan_ranges null`, `vlan_has_range false`.

Member (mode inferred, no `switchport mode` line):
```
interface GigabitEthernet1/0/7
 description Uplink zu Core
 switchport trunk native vlan 101
 switchport trunk allowed vlan 5,100-200,204,205
 channel-group 2 mode active
```
-> `kind member`, `mode tagged`, `untagged_vlan 101`,
`tagged_vlans [5, 100, 204, 205]`, `tagged_vlan_ranges ["102-200"]`,
`vlan_has_range true`, `channel_group 2`, `channel_group_mode "active"`.

Port-channel without any switchport line (`interface Port-channel7`):
-> `kind channel`, `mode null`, all VLAN fields null, `vlan_has_range false`,
flags false.

Empty physical port (`interface GigabitEthernet1/0/1` with no lines):
-> `kind unconfigured`, everything null/false.

## 6. Implementation notes

- No parser or custom filter is needed for reading the device. Only the mapping
  of section 4 has to be implemented, in whatever form fits the TextFSM output
  (for example a small function or Jinja logic).
- The VLAN handling of rule 4.4 is the part most likely to drift. Its exact
  semantics are in `expand_vlans` and `split_ranges` in
  `roles/netconf/port/facts/filter_plugins/port_facts.py` (constant
  `MIN_RANGE = 4`); reproduce them exactly.
- Use the same fact and variable names as `netconf/port/facts`
  (`port_facts_all`, `port_facts_access`, `port_facts_trunk`,
  `port_facts_member`, `port_facts_channel`, `port_facts_unconfigured`,
  `port_facts_expand_vlans`), so playbooks can swap the role.

## 7. Acceptance test

- Write pytest cases from the examples in section 5 (as TextFSM records) and add edge cases:
  `allowed vlan none`, `allowed vlan add`, `allowed vlan except`, `mode dynamic`,
  an access port without `switchport access vlan`, a run of exactly 3 and
  exactly 4 consecutive VLANs, native VLAN inside a range, `expand=true`.
- **Conformance check:** take TextFSM records that are equivalent to
  `xml_example/all_interfaces.xml` (the 1/0/x ports and the Port-channels) and
  assert that the mapping returns the **same list of dicts** as
  `port_facts(<that xml>)`, compared as sorted JSON.
- Run `uv run ruff check`, `uv run ruff format`, `uv run pytest` and
  `uv run ansible-lint`; they must pass.
