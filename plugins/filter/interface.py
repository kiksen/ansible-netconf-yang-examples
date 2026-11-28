"""Jinja filters to split Cisco interface names."""

import re
from enum import StrEnum
from typing import NamedTuple

from ansible.errors import AnsibleFilterError

_INTERFACE_RE = re.compile(
    r"^(?P<type>[A-Za-z][A-Za-z-]*?)\s*(?P<numbers>\d+(?:/\d+)*)$"
)


_KNOWN_TYPES: dict[str, str] = {
    t.lower(): t
    for t in (
        "FastEthernet",
        "GigabitEthernet",
        "TenGigabitEthernet",
        "TwentyFiveGigE",
        "FortyGigabitEthernet",
        "HundredGigE",
        "Port-channel",
        "Vlan",
        "BDI",
        "Loopback",
        "Tunnel",
    )
}


_ALIASES: dict[str, str] = {
    "fa": "FastEthernet",
    "gi": "GigabitEthernet",
    "gig": "GigabitEthernet",
    "te": "TenGigabitEthernet",
    "ten": "TenGigabitEthernet",
    "twe": "TwentyFiveGigE",
    "fo": "FortyGigabitEthernet",
    "hu": "HundredGigE",
    "po": "Port-channel",
    "vl": "Vlan",
    "lo": "Loopback",
    "tu": "Tunnel",
}


def normalize_type(name: str) -> str:
    """Return the Cisco spelling of a type, e.g. 'port-CHANNEL' -> 'Port-channel'.

    Common abbreviations such as 'Gi' or 'po' are resolved.

    Unknown types are returned unchanged.
    """
    key = name.lower()
    return _KNOWN_TYPES.get(key) or _ALIASES.get(key, name)


class Part(StrEnum):
    """Bestandteile eines Interface-Namens."""

    TYPE = "type"
    SWITCH = "switch"
    SLOT = "slot"
    SUBSLOT = "subslot"
    PORT = "port"
    ID = "id"


class Interface(NamedTuple):
    """Parsed interface name; missing parts are None."""

    type: str
    switch: str | None
    slot: str | None
    subslot: str | None
    port: str
    id: str


def parse_interface(name: str, normalize: bool = True) -> Interface:
    """Split e.g. 'GigabitEthernet1/2/3/4' into type, switch, slot, subslot, port and id.

    The id is the complete numeric part ('1/2/3/4', '1/0' or '1').
    The numbers are assigned from the right: port, subslot, slot, switch.
    With normalize=False the type stays as it was written.
    So 'Gi1/0/5' has switch=1, slot=0, port=5 and no subslot.
    """
    match = _INTERFACE_RE.match(name.strip())
    if match is None:
        raise ValueError(f"Ungueltiger Interface-Name: {name!r}")
    numbers = match["numbers"].split("/")
    if len(numbers) > 4:
        raise ValueError(f"Zu viele Ebenen im Interface-Namen: {name!r}")
    port = numbers.pop()
    switch, slot, subslot = (None, None, None)
    if len(numbers) == 1:
        slot = numbers[0]
    elif len(numbers) == 2:
        switch, slot = numbers
    elif len(numbers) == 3:
        switch, slot, subslot = numbers
    type_ = normalize_type(match["type"]) if normalize else match["type"]
    return Interface(type_, switch, slot, subslot, port, match["numbers"])


def interface_part(name: str, part: str, normalize: bool = True) -> str | None:
    """Jinja filter: return one part of the interface name.

    Example: ``"GigabitEthernet1/0/5" | interface_part("port")`` gives ``"5"``.
    If the part is missing in the name, None is returned.
    With ``normalize=False`` the type is not converted to the Cisco spelling
    (no case correction, no abbreviations).
    """
    try:
        wanted = Part(part)
        return getattr(parse_interface(str(name), normalize), wanted.value)
    except ValueError as err:
        raise AnsibleFilterError(f"interface_part: {err}") from err


class RepSegment(NamedTuple):
    """REP settings derived from an interface name."""

    id: int
    edge: bool
    no_neighbor: bool
    primary: bool
    preferred: bool


def rep_segment(name: str) -> dict[str, int | bool]:
    """Jinja filter: derive the REP segment data from the interface name.

    The segment ID is the port number ('1/0/5' -> 5). The role comes from the switch:
    switch 1 is the active Flexlink+ port (edge no-neighbor primary), switch 2
    the standby port (edge no-neighbor preferred). Other switch numbers and
    names without a switch number (e.g. 'Gi0') are invalid.
    """
    try:
        parsed = parse_interface(str(name))
        if parsed.switch is None:
            raise ValueError(f"Interface without a switch number: {name!r}")
        switch = int(parsed.switch)
        if switch not in (1, 2):
            raise ValueError(f"REP is only intended for switch 1 and 2: {name!r}")
        segment = RepSegment(
            id=int(parsed.port),
            edge=True,
            no_neighbor=True,
            primary=switch == 1,
            preferred=switch == 2,
        )
    except ValueError as err:
        raise AnsibleFilterError(f"rep_segment: {err}") from err
    return segment._asdict()


class FilterModule:
    """Register the filters with Ansible."""

    def filters(self) -> dict[str, object]:
        """Return the available filters."""
        return {"interface_part": interface_part, "rep_segment": rep_segment}
