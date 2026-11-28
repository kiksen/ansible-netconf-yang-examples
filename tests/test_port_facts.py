"""Tests for the filter port_facts."""

from pathlib import Path

import pytest
from ansible.errors import AnsibleFilterError
from port_facts import expand_vlans, port_facts, split_ranges

_EXAMPLE = Path(__file__).parent.parent / "xml_example" / "all_interfaces.xml"


@pytest.fixture(scope="module")
def ports() -> dict[str, dict[str, object]]:
    """Return the parsed lab reply keyed by interface name."""
    facts = port_facts(_EXAMPLE.read_text())
    return {str(port["interface"]): port for port in facts}


def _wrap(trunk_body: str) -> str:
    """Build a minimal reply with one trunk port around the given trunk body."""
    return f"""
    <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native"><interface>
        <GigabitEthernet><name>1/0/9</name><switchport-config><switchport>
          <mode xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-switch"><trunk/></mode>
          <trunk xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-switch">{trunk_body}</trunk>
        </switchport></switchport-config></GigabitEthernet>
      </interface></native>
    </data>"""


def test_access_port_with_voice_vlan(ports: dict[str, dict[str, object]]) -> None:
    """An access port reports untagged and voice VLAN."""
    port = ports["GigabitEthernet1/0/2"]
    assert port["kind"] == "access"
    assert port["mode"] == "access"
    assert port["description"] == "Arbeitsplatz"
    assert port["untagged_vlan"] == 123
    assert port["voice_vlan"] == 500
    assert port["tagged_vlans"] is None


def test_access_port_without_voice_vlan_is_none(
    ports: dict[str, dict[str, object]],
) -> None:
    """A missing voice VLAN is reported as None."""
    assert ports["GigabitEthernet1/0/3"]["voice_vlan"] is None


def test_cdp_lldp_flags(ports: dict[str, dict[str, object]]) -> None:
    """Disabled CDP and LLDP are reported as no_* flags."""
    port = ports["GigabitEthernet1/0/4"]
    assert port["no_cdp_enable"] is True
    assert port["no_lldp_transmit"] is True
    assert port["no_lldp_receive"] is True
    assert ports["GigabitEthernet1/0/2"]["no_cdp_enable"] is False


def test_trunk_native_vlan_is_not_tagged(ports: dict[str, dict[str, object]]) -> None:
    """The native VLAN is untagged and removed from the tagged list."""
    port = ports["GigabitEthernet1/0/6"]
    assert port["kind"] == "trunk"
    assert port["mode"] == "tagged"
    assert port["untagged_vlan"] == 100
    assert port["tagged_vlans"] == [200, 300]


def test_trunk_without_allowed_is_tagged_all(
    ports: dict[str, dict[str, object]],
) -> None:
    """A trunk without allowed list permits all VLANs."""
    port = ports["GigabitEthernet1/0/8"]
    assert port["kind"] == "trunk"
    assert port["mode"] == "tagged-all"
    assert port["tagged_vlans"] is None
    assert port["untagged_vlan"] == 1


def test_member_reports_channel_group(ports: dict[str, dict[str, object]]) -> None:
    """A port with channel-group is a member even if it holds trunk config."""
    port = ports["GigabitEthernet1/0/7"]
    assert port["kind"] == "member"
    assert port["channel_group"] == 2
    assert port["channel_group_mode"] == "active"
    assert port["mode"] == "tagged"
    assert port["vlan_has_range"] is True


def test_port_channels(ports: dict[str, dict[str, object]]) -> None:
    """Port-channels are kind channel; mode is inferred without explicit mode."""
    assert ports["Port-channel2"]["kind"] == "channel"
    assert ports["Port-channel2"]["tagged_vlans"] == [5, 100, 204, 205]
    assert ports["Port-channel2"]["tagged_vlan_ranges"] == ["102-200"]
    assert ports["Port-channel2"]["vlan_has_range"] is True
    assert ports["Port-channel30"]["mode"] == "access"
    assert ports["Port-channel30"]["untagged_vlan"] == 123
    assert ports["Port-channel7"]["mode"] is None


def test_unconfigured_and_skipped(ports: dict[str, dict[str, object]]) -> None:
    """Ports without config are unconfigured; Vlan interfaces are skipped."""
    assert ports["GigabitEthernet1/0/1"]["kind"] == "unconfigured"
    assert ports["GigabitEthernet1/0/1"]["mode"] is None
    assert not any(name.startswith("Vlan") for name in ports)


def test_kinds_filter() -> None:
    """The kinds argument limits the result."""
    result = port_facts(_EXAMPLE.read_text(), ["member", "channel"])
    assert {port["kind"] for port in result} == {"member", "channel"}


@pytest.mark.parametrize(
    ("body", "mode", "tagged"),
    [
        (
            "<allowed><vlan-v2><vlan-choices><all/></vlan-choices></vlan-v2></allowed>",
            "tagged-all",
            None,
        ),
        (
            "<allowed><vlan-v2><vlan-choices><none/></vlan-choices></vlan-v2></allowed>",
            "tagged",
            [],
        ),
        (
            "<allowed><vlan-v2><vlan-choices><vlans>10-11</vlans><add>20</add></vlan-choices></vlan-v2></allowed>",
            "tagged",
            [10, 11, 20],
        ),
    ],
)
def test_allowed_choices(body: str, mode: str, tagged: list[int] | None) -> None:
    """The allowed VLAN choices map to mode and tagged list."""
    [port] = port_facts(_wrap(body))
    assert port["mode"] == mode
    assert port["tagged_vlans"] == tagged


def test_expand_vlans_rejects_out_of_range() -> None:
    """VLAN IDs outside 1-4094 are rejected."""
    with pytest.raises(ValueError, match="Invalid VLAN range"):
        expand_vlans("4095")


def test_invalid_xml_raises_filter_error() -> None:
    """Broken XML becomes an AnsibleFilterError."""
    with pytest.raises(AnsibleFilterError):
        port_facts("<data")


def test_expand_lists_every_vlan() -> None:
    """With expand=True all VLANs are listed and no range is reported."""
    result = {
        str(port["interface"]): port
        for port in port_facts(_EXAMPLE.read_text(), expand=True)
    }
    port = result["Port-channel2"]
    assert port["tagged_vlans"] == [5, *range(100, 101), *range(102, 201), 204, 205]
    assert port["tagged_vlan_ranges"] == []
    assert port["vlan_has_range"] is False


@pytest.mark.parametrize(
    ("vlans", "singles", "ranges"),
    [
        ([], [], []),
        ([10, 11, 12], [10, 11, 12], []),
        ([10, 11, 12, 13], [], ["10-13"]),
        ([5, 10, 11, 12, 13, 20], [5, 20], ["10-13"]),
        ([1, 2, 3, 4, 6, 7, 8, 9, 10], [], ["1-4", "6-10"]),
    ],
)
def test_split_ranges(vlans: list[int], singles: list[int], ranges: list[str]) -> None:
    """Only runs of at least four consecutive VLANs become a range."""
    assert split_ranges(vlans) == (singles, ranges)


def test_access_and_tagged_all_have_no_ranges(
    ports: dict[str, dict[str, object]],
) -> None:
    """Ports without a tagged list report no ranges."""
    for name in ("GigabitEthernet1/0/2", "GigabitEthernet1/0/8"):
        assert ports[name]["tagged_vlan_ranges"] is None
        assert ports[name]["vlan_has_range"] is False


def test_enabled_flag_follows_shutdown_element() -> None:
    """A port is disabled only when it carries a shutdown element."""
    xml = _wrap("")
    assert port_facts(xml)[0]["enabled"] is True
    shut = xml.replace("<name>1/0/9</name>", "<name>1/0/9</name><shutdown/>")
    assert port_facts(shut)[0]["enabled"] is False
