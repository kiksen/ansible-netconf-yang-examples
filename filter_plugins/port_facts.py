"""Jinja filter that turns a Cisco-IOS-XE-native interface reply into port facts."""

from dataclasses import asdict, dataclass
from enum import StrEnum

from ansible.errors import AnsibleFilterError
from lxml import etree
from lxml.etree import _Element as Element

VLAN_MIN = 1
VLAN_MAX = 4094

# Interface containers below native/interface that carry no switchport facts.
_SKIPPED_TYPES = frozenset({"Vlan", "Loopback", "Tunnel", "Null", "BDI"})


class Kind(StrEnum):
    """Role of a port, derived from its configuration."""

    ACCESS = "access"
    TRUNK = "trunk"
    MEMBER = "member"
    CHANNEL = "channel"
    UNCONFIGURED = "unconfigured"


class Mode(StrEnum):
    """VLAN mode using the NetBox names."""

    ACCESS = "access"
    TAGGED = "tagged"
    TAGGED_ALL = "tagged-all"


@dataclass(frozen=True, slots=True)
class PortFacts:
    """Facts of a single interface."""

    interface: str
    kind: Kind
    mode: Mode | None
    description: str | None
    untagged_vlan: int | None
    voice_vlan: int | None
    tagged_vlans: list[int] | None
    no_cdp_enable: bool
    no_lldp_transmit: bool
    no_lldp_receive: bool
    channel_group: int | None
    channel_group_mode: str | None


def _local(element: Element) -> str:
    """Return the tag name of an element without its namespace."""
    return etree.QName(element).localname


def _text(parent: Element | None, path: str) -> str | None:
    """Return the stripped text of the element at ``path`` below ``parent``."""
    if parent is None:
        return None
    found = parent.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip()


def _int(parent: Element | None, path: str) -> int | None:
    """Return the integer value of the element at ``path`` or None."""
    value = _text(parent, path)
    return int(value) if value else None


def expand_vlans(value: str) -> list[int]:
    """Expand a VLAN string such as '5,100-102' into a sorted list of unique IDs."""
    vlans: set[int] = set()
    for token in value.replace(" ", "").split(","):
        if not token:
            continue
        low_text, sep, high_text = token.partition("-")
        low = int(low_text)
        high = int(high_text) if sep else low
        if not VLAN_MIN <= low <= high <= VLAN_MAX:
            raise ValueError(f"Invalid VLAN range {token!r}")
        vlans.update(range(low, high + 1))
    return sorted(vlans)


def _allowed_vlans(trunk: Element | None) -> tuple[Mode, list[int] | None]:
    """Return the trunk VLAN mode and the tagged VLAN list of a trunk element.

    A trunk without an ``allowed`` node permits all VLANs (tagged-all). The
    choices ``vlans`` and ``add`` are merged, ``none`` yields an empty list and
    ``except`` yields every VLAN but the listed ones.
    """
    choices = (
        None if trunk is None else trunk.find("{*}allowed/{*}vlan-v2/{*}vlan-choices")
    )
    if choices is None:
        return Mode.TAGGED_ALL, None
    if choices.find("{*}all") is not None:
        return Mode.TAGGED_ALL, None
    if choices.find("{*}none") is not None:
        return Mode.TAGGED, []
    except_text = _text(choices, "{*}except")
    if except_text is not None:
        excluded = set(expand_vlans(except_text))
        return Mode.TAGGED, [
            v for v in range(VLAN_MIN, VLAN_MAX + 1) if v not in excluded
        ]
    listed = {
        vlan
        for tag in ("vlans", "add")
        for vlan in expand_vlans(_text(choices, f"{{*}}{tag}") or "")
    }
    return Mode.TAGGED, sorted(listed)


def _switchport_mode(switchport: Element | None) -> str | None:
    """Return 'access' or 'trunk' from the switchport config, inferring a missing mode."""
    if switchport is None:
        return None
    explicit = switchport.find("{*}mode")
    if explicit is not None:
        if explicit.find("{*}trunk") is not None:
            return "trunk"
        if explicit.find("{*}access") is not None:
            return "access"
    if switchport.find("{*}trunk") is not None:
        return "trunk"
    if switchport.find("{*}access") is not None:
        return "access"
    return None


def _parse_interface(entry: Element) -> PortFacts:
    """Build the facts of one interface entry below native/interface.

    The tag of the entry is the interface type, e.g. ``GigabitEthernet``.
    """
    type_name = _local(entry)
    name = f"{type_name}{_text(entry, '{*}name')}"
    switchport = entry.find("{*}switchport-config/{*}switchport")
    sw_mode = _switchport_mode(switchport)

    mode: Mode | None = None
    untagged: int | None = None
    tagged: list[int] | None = None
    if sw_mode == "access":
        mode = Mode.ACCESS
        untagged = _int(switchport, "{*}access/{*}vlan/{*}vlan")
    elif sw_mode == "trunk":
        trunk = switchport.find("{*}trunk") if switchport is not None else None
        untagged = _int(trunk, "{*}native/{*}vlan/{*}vlan-id")
        mode, tagged = _allowed_vlans(trunk)
        if tagged is not None and untagged is not None:
            tagged = [vlan for vlan in tagged if vlan != untagged]

    group = entry.find("{*}channel-group")
    group_number = _int(group, "{*}number")
    if type_name == "Port-channel":
        kind = Kind.CHANNEL
    elif group_number is not None:
        kind = Kind.MEMBER
    elif sw_mode == "trunk":
        kind = Kind.TRUNK
    elif sw_mode == "access":
        kind = Kind.ACCESS
    else:
        kind = Kind.UNCONFIGURED

    return PortFacts(
        interface=name,
        kind=kind,
        mode=mode,
        description=_text(entry, "{*}description"),
        untagged_vlan=untagged,
        voice_vlan=_int(switchport, "{*}voice/{*}vlan/{*}vlan"),
        tagged_vlans=tagged,
        no_cdp_enable=_text(entry, "{*}cdp/{*}enable") == "false",
        no_lldp_transmit=_text(entry, "{*}lldp/{*}transmit") == "false",
        no_lldp_receive=_text(entry, "{*}lldp/{*}receive") == "false",
        channel_group=group_number,
        channel_group_mode=_text(group, "{*}mode"),
    )


def parse_ports(xml: str) -> list[PortFacts]:
    """Parse a get/get-config reply containing native/interface into port facts."""
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(xml.encode(), parser)
    ports: list[PortFacts] = []
    for entry in root.iterfind(".//{*}native/{*}interface/*"):
        name = _text(entry, "{*}name")
        if _local(entry) in _SKIPPED_TYPES or name is None or "." in name:
            continue  # no switchport facts or sub-interface
        ports.append(_parse_interface(entry))
    return ports


def port_facts(xml: str, kinds: list[str] | None = None) -> list[dict[str, object]]:
    """Jinja filter: return the port facts of a native interface reply as dicts.

    ``kinds`` limits the result to the given kinds (access, trunk, member,
    channel, unconfigured). Example: ``reply.stdout | port_facts(['trunk'])``.
    """
    try:
        wanted = {Kind(kind) for kind in kinds} if kinds is not None else None
        ports = parse_ports(str(xml))
    except (ValueError, etree.XMLSyntaxError) as err:
        raise AnsibleFilterError(f"port_facts: {err}") from err
    return [
        {
            key: str(value) if isinstance(value, StrEnum) else value
            for key, value in asdict(port).items()
        }
        for port in ports
        if wanted is None or port.kind in wanted
    ]


class FilterModule:
    """Register the filter with Ansible."""

    def filters(self) -> dict[str, object]:
        """Return the available filters."""
        return {"port_facts": port_facts}
