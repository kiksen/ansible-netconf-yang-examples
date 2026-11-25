"""Jinja-Filter zum Normalisieren von VLAN-Listen und -Ranges."""

from ansible.errors import AnsibleFilterError

VLAN_MIN = 1
VLAN_MAX = 4094

type VlanInput = int | str | list[int | str]


def _parse_token(token: str) -> tuple[int, int]:
    """Wandelt '20' oder '20-30' in ein Intervall (lo, hi) um."""
    low_text, sep, high_text = token.partition("-")
    try:
        low = int(low_text)
        high = int(high_text) if sep else low
    except ValueError as err:
        raise ValueError(f"Ungueltige VLAN-Angabe: {token!r}") from err
    if not VLAN_MIN <= low <= high <= VLAN_MAX:
        raise ValueError(
            f"VLAN-Bereich {token!r} ausserhalb von {VLAN_MIN}-{VLAN_MAX} "
            "oder in falscher Reihenfolge"
        )
    return low, high


def parse_vlans(value: VlanInput) -> list[tuple[int, int]]:
    """Zerlegt VLAN-Angaben in sortierte, zusammengefasste Intervalle.

    Erlaubt sind int, Strings wie '1,20-30' und Listen aus beidem.
    Ueberlappende und direkt benachbarte Werte werden verschmolzen.
    """
    items = value if isinstance(value, list) else [value]
    intervals: list[tuple[int, int]] = []
    for item in items:
        if isinstance(item, bool):
            raise TypeError(f"Ungueltige VLAN-Angabe: {item!r}")
        for token in str(item).replace(" ", "").split(","):
            if not token:
                raise ValueError(f"Leere VLAN-Angabe in {value!r}")
            intervals.append(_parse_token(token))
    merged: list[tuple[int, int]] = []
    for low, high in sorted(intervals):
        if merged and low <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged


def vlan_list(value: VlanInput) -> str:
    """Jinja-Filter: normalisiert VLANs zu einem String wie '1,20-30,100'.

    Beispiel: ``[1, "20-30", 21, 100] | vlan_list`` ergibt ``"1,20-30,100"``.
    """
    try:
        intervals = parse_vlans(value)
    except (TypeError, ValueError) as err:
        raise AnsibleFilterError(f"vlan_list: {err}") from err
    return ",".join(
        str(low) if low == high else f"{low}-{high}" for low, high in intervals
    )


class FilterModule:
    """Registriert die Filter bei Ansible."""

    def filters(self) -> dict[str, object]:
        """Liefert die verfuegbaren Filter."""
        return {"vlan_list": vlan_list}
