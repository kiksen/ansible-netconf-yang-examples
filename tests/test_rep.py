"""Tests fuer den Filter rep_segment."""

import pytest
from ansible.errors import AnsibleFilterError
from interface import rep_segment


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "GigabitEthernet1/0/5",
            {
                "id": 5,
                "edge": True,
                "no_neighbor": True,
                "primary": True,
                "preferred": False,
            },
        ),
        (
            "Gi2/0/5",
            {
                "id": 5,
                "edge": True,
                "no_neighbor": True,
                "primary": False,
                "preferred": True,
            },
        ),
    ],
)
def test_rep_segment(name: str, expected: dict[str, int | bool]) -> None:
    """Segment-ID kommt vom Port, edge/primary vom Switch."""
    assert rep_segment(name) == expected


@pytest.mark.parametrize("name", ["Gi5", "foo", "Te3/0/1"])
def test_rep_segment_invalid(name: str) -> None:
    """Ohne Switch-Nummer oder ungueltig gibt es einen Fehler."""
    with pytest.raises(AnsibleFilterError):
        rep_segment(name)
