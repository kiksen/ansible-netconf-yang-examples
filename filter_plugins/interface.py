"""Jinja-Filter zum Zerlegen von Cisco-Interface-Namen."""

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
    """Liefert die Cisco-Schreibweise eines Typs, z.B. 'port-CHANNEL' -> 'Port-channel'.

    Gaengige Abkuerzungen wie 'Gi' oder 'po' werden aufgeloest.

    Unbekannte Typen werden unveraendert zurueckgegeben.
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
    """Zerlegter Interface-Name; nicht vorhandene Teile sind None."""

    type: str
    switch: str | None
    slot: str | None
    subslot: str | None
    port: str
    id: str


def parse_interface(name: str, normalize: bool = True) -> Interface:
    """Zerlegt z.B. 'GigabitEthernet1/2/3/4' in type, switch, slot, subslot, port und id.

    Die id ist der komplette Zahlenteil ('1/2/3/4', '1/0' oder '1').
    Die Zahlen werden von rechts zugeordnet: port, subslot, slot, switch.
    Mit normalize=False bleibt der Typ so, wie er geschrieben wurde.
    'Gi1/0/5' hat damit switch=1, slot=0, port=5 und keinen subslot.
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
    """Jinja-Filter: gibt einen Teil des Interface-Namens zurueck.

    Beispiel: ``"GigabitEthernet1/0/5" | interface_part("port")`` ergibt ``"5"``.
    Fehlt der Teil im Namen, wird None zurueckgegeben.
    Mit ``normalize=False`` wird der Typ nicht in die Cisco-Schreibweise
    umgewandelt (keine Gross-/Kleinschreibung-Korrektur, keine Abkuerzungen).
    """
    try:
        wanted = Part(part)
        return getattr(parse_interface(str(name), normalize), wanted.value)
    except ValueError as err:
        raise AnsibleFilterError(f"interface_part: {err}") from err


class FilterModule:
    """Registriert die Filter bei Ansible."""

    def filters(self) -> dict[str, object]:
        """Liefert die verfuegbaren Filter."""
        return {"interface_part": interface_part}
