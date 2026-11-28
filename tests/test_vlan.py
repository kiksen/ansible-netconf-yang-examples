"""Tests for the filter vlan_list."""

import pytest
from ansible.errors import AnsibleFilterError
from vlan import vlan_list, with_native_vlan


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100, "100"),
        ("2-4094", "2-4094"),
        ("1,20-30", "1,20-30"),
        ([100, 200, 300], "100,200,300"),
        ([1, "20-30", 100], "1,20-30,100"),
        ([1, 2, 3], "1-3"),
        ([30, "20-25", 26, 22, 100], "20-26,30,100"),
        ("10-20, 15-25", "10-25"),
    ],
)
def test_vlan_list(value: int | str | list[int | str], expected: str) -> None:
    """Normalizes single values, ranges and mixed forms."""
    assert vlan_list(value) == expected


@pytest.mark.parametrize(
    "value", [0, 4095, "30-20", "abc", "1-", "1,,2", "", True, [1, None]]
)
def test_vlan_list_invalid(value: object) -> None:
    """Invalid values raise AnsibleFilterError."""
    with pytest.raises(AnsibleFilterError):
        vlan_list(value)  # type: ignore[arg-type]  # intentionally invalid


@pytest.mark.parametrize(
    ("allowed", "native", "expected"),
    [
        ("all", 10, "all"),
        ([100, 200], None, "100,200"),
        ([100, 200], 10, "10,100,200"),
        ("100-200", 150, "100-200"),
        ("5,100-200", 10, "5,10,100-200"),
        ([100], "", "100"),
    ],
)
def test_with_native_vlan(
    allowed: int | str | list[int | str], native: int | None, expected: str
) -> None:
    """The native VLAN ends up in the allowed list, 'all' stays unchanged."""
    result = with_native_vlan(allowed, native)
    assert (result if result == "all" else vlan_list(result)) == expected
