"""Tests fuer den Filter vlan_list."""

import pytest
from ansible.errors import AnsibleFilterError
from vlan import vlan_list


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
    """Normalisiert Einzelwerte, Ranges und Mischformen."""
    assert vlan_list(value) == expected


@pytest.mark.parametrize(
    "value", [0, 4095, "30-20", "abc", "1-", "1,,2", "", True, [1, None]]
)
def test_vlan_list_invalid(value: object) -> None:
    """Ungueltige Angaben loesen AnsibleFilterError aus."""
    with pytest.raises(AnsibleFilterError):
        vlan_list(value)  # type: ignore[arg-type]  # absichtlich ungueltig
