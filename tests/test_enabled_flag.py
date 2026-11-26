"""Tests for the enabled flag in the interface templates."""

from pathlib import Path

import pytest
from interface import interface_part, rep_segment
from jinja2 import Environment, FileSystemLoader

_PORT_ROLES = Path(__file__).parent.parent / "roles" / "netconf" / "port"

# role directory, template, variable prefix, extra variables needed to render
_CASES = [
    (
        "access",
        "access_port.xml.j2",
        "port_access",
        {"interface": "Gi1/0/5", "vlan": 10, "description": "pc", "voice_vlan": None},
    ),
    (
        "trunk",
        "trunk_port.xml.j2",
        "port_trunk",
        {"interface": "Gi1/0/5", "description": "up", "allowed_vlans": [10]},
    ),
    (
        "channel",
        "port_channel.xml.j2",
        "port_channel",
        {"interface": "Po1", "description": "lag", "allowed_vlans": [10]},
    ),
    (
        "channel_member",
        "channel_member.xml.j2",
        "port_channel_member",
        {"interface": "Gi1/0/5", "number": 1, "mode": "active"},
    ),
]


def _render(
    role: str, template: str, prefix: str, extra: dict[str, object], enabled: bool
) -> str:
    """Render a role template with the given enabled value."""
    env = Environment(
        loader=FileSystemLoader(_PORT_ROLES / role / "templates"), autoescape=False
    )
    env.filters["interface_part"] = interface_part
    env.filters["rep_segment"] = rep_segment
    env.filters["vlan_list"] = lambda vlans: ",".join(str(v) for v in vlans)
    defaults = {
        "native_vlan": None,
        "voice_vlan": None,
        "description": None,
        "no_cdp_enable": None,
        "no_lldp_transmit": None,
        "no_lldp_receive": None,
        "rep": None,
        "nonegotiate": None,
        "service_policy_out": "QUEUE-OUT",
    }
    variables = {f"{prefix}_{k}": v for k, v in (defaults | extra).items()}
    variables[f"{prefix}_enabled"] = enabled
    return env.get_template(template).render(**variables)


@pytest.mark.parametrize(("role", "template", "prefix", "extra"), _CASES)
def test_disabled_writes_shutdown(
    role: str, template: str, prefix: str, extra: dict[str, object]
) -> None:
    """A disabled interface gets <shutdown/>."""
    xml = _render(role, template, prefix, extra, enabled=False)
    assert "<shutdown/>" in xml
    assert 'nc:operation="remove"' not in xml.split("<shutdown")[1].split(">")[0]


@pytest.mark.parametrize(("role", "template", "prefix", "extra"), _CASES)
def test_enabled_has_no_shutdown(
    role: str, template: str, prefix: str, extra: dict[str, object]
) -> None:
    """An enabled interface never carries a plain <shutdown/>."""
    xml = _render(role, template, prefix, extra, enabled=True)
    assert "<shutdown/>" not in xml


def test_shutdown_role_template() -> None:
    """The shutdown role writes only the name and <shutdown/>."""
    xml = _render(
        "shutdown",
        "shutdown.xml.j2",
        "port_shutdown",
        {"interface": "Gi1/1/1"},
        enabled=False,
    )
    assert "<shutdown/>" in xml
    assert "<name>1/1/1</name>" in xml
    assert "description" not in xml
