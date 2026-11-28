"""Jinja filters to normalize VLAN lists and ranges."""

from ansible.errors import AnsibleFilterError

VLAN_MIN = 1
VLAN_MAX = 4094

type VlanInput = int | str | list[int | str]


def _parse_token(token: str) -> tuple[int, int]:
    """Convert '20' or '20-30' into an interval (lo, hi)."""
    low_text, sep, high_text = token.partition("-")
    try:
        low = int(low_text)
        high = int(high_text) if sep else low
    except ValueError as err:
        raise ValueError(f"Invalid VLAN value: {token!r}") from err
    if not VLAN_MIN <= low <= high <= VLAN_MAX:
        raise ValueError(
            f"VLAN-Bereich {token!r} outside of {VLAN_MIN}-{VLAN_MAX} "
            "or in the wrong order"
        )
    return low, high


def parse_vlans(value: VlanInput) -> list[tuple[int, int]]:
    """Split VLAN values into sorted, merged intervals.

    Accepts int, strings such as '1,20-30' and lists of both.
    Overlapping and directly adjacent values are merged.
    """
    items = value if isinstance(value, list) else [value]
    intervals: list[tuple[int, int]] = []
    for item in items:
        if isinstance(item, bool):
            raise TypeError(f"Invalid VLAN value: {item!r}")
        for token in str(item).replace(" ", "").split(","):
            if not token:
                raise ValueError(f"Empty VLAN value in {value!r}")
            intervals.append(_parse_token(token))
    merged: list[tuple[int, int]] = []
    for low, high in sorted(intervals):
        if merged and low <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged


def vlan_list(value: VlanInput) -> str:
    """Jinja filter: normalize VLANs to a string such as '1,20-30,100'.

    Example: ``[1, "20-30", 21, 100] | vlan_list`` gives ``"1,20-30,100"``.
    """
    try:
        intervals = parse_vlans(value)
    except (TypeError, ValueError) as err:
        raise AnsibleFilterError(f"vlan_list: {err}") from err
    return ",".join(
        str(low) if low == high else f"{low}-{high}" for low, high in intervals
    )


def with_native_vlan(allowed: VlanInput, native: int | str | None) -> VlanInput:
    """Jinja filter: add the native VLAN to the allowed list of a trunk.

    'all' stays 'all'; without a native VLAN the list is unchanged.
    Merging and deduplication is done afterwards by ``vlan_list``.
    """
    if allowed == "all" or native is None or native == "":
        return allowed
    items = allowed if isinstance(allowed, list) else [allowed]
    return [*items, native]


class FilterModule:
    """Register the filters with Ansible."""

    def filters(self) -> dict[str, object]:
        """Return the available filters."""
        return {"vlan_list": vlan_list, "with_native_vlan": with_native_vlan}
