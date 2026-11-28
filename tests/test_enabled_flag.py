"""Tests for the enabled flag in the interface templates."""

from pathlib import Path

import pytest
from interface import interface_part, rep_segment
from jinja2 import Environment, FileSystemLoader

_ROLES = Path(__file__).parent.parent / "roles"

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
        loader=FileSystemLoader(_ROLES / f"port_{role}" / "templates"), autoescape=False
    )
    env.filters["kiksen.netconf.interface_part"] = interface_part
    env.filters["kiksen.netconf.rep_segment"] = rep_segment
    env.filters["kiksen.netconf.vlan_list"] = lambda vlans: ",".join(
        str(v) for v in vlans
    )
    defaults = {
        "native_vlan": None,
        "mode": "trunk",
        "access_vlan": None,
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


def test_channel_access_mode_has_no_trunk_or_snooping() -> None:
    """An access port-channel writes the access VLAN, no trunk block and no DHCP trust."""
    xml = _render(
        "channel",
        "port_channel.xml.j2",
        "port_channel",
        {"interface": "Po30", "mode": "access", "access_vlan": 123},
        enabled=True,
    )
    assert "<access/>" in xml
    assert "<vlan>123</vlan>" in xml
    assert "<trunk" not in xml
    assert "snooping" not in xml
    assert "<storm-control>" in xml


def test_channel_trunk_mode_keeps_trunk_and_snooping() -> None:
    """The default mode still writes the trunk block and DHCP snooping trust."""
    xml = _render(
        "channel",
        "port_channel.xml.j2",
        "port_channel",
        {"interface": "Po2", "allowed_vlans": [10], "native_vlan": 101},
        enabled=True,
    )
    assert "<trunk/>" in xml
    assert "<vlan-id>101</vlan-id>" in xml
    assert "snooping" in xml


def _render_vlans(vlans: list[dict[str, object]], operation: str = "replace") -> str:
    """Render the VLAN template for the given VLAN list and operation."""
    env = Environment(
        loader=FileSystemLoader(_ROLES / "system_vlan" / "templates"),
        autoescape=False,
    )
    return env.get_template("vlan.xml.j2").render(
        system_vlan_list=vlans, system_vlan_operation=operation
    )


def test_vlan_template_replaces_container_and_skips_vlan_1() -> None:
    """The VLAN container is replaced, sorted by ID, and VLAN 1 is not written."""
    xml = _render_vlans(
        [{"vid": 200, "name": "Servers"}, {"vid": 1, "name": "default"}, {"vid": 100}]
    )
    assert '<vlan nc:operation="replace">' in xml
    assert "<id>1</id>" not in xml
    assert xml.index("<id>100</id>") < xml.index("<id>200</id>")
    assert "<name>Servers</name>" in xml
    assert xml.count("<name>") == 1


def test_vlan_template_merge_has_no_replace() -> None:
    """The merge operation leaves out the replace operation on the VLAN container."""
    xml = _render_vlans([{"vid": 100, "name": "Clients"}], operation="merge")
    assert "nc:operation" not in xml
    assert "<id>100</id>" in xml
