"""Tests for the filter system_facts."""

import pytest
from ansible.errors import AnsibleFilterError
from system_facts import system_facts

_REPLY = """
<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <hostname>sw1</hostname>
    <version>17.9</version>
  </native>
  <device-hardware-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-device-hardware-oper">
    <device-hardware>
      <device-inventory>
        <hw-type>hw-type-chassis</hw-type>
        <hw-dev-index>0</hw-dev-index>
        <dev-name>Switch 1</dev-name>
        <part-number>C9300-24P</part-number>
        <serial-number>FCW1234</serial-number>
        <field-replaceable>false</field-replaceable>
      </device-inventory>
      <device-inventory>
        <hw-type>hw-type-power-supply</hw-type>
        <hw-dev-index>1</hw-dev-index>
        <serial-number>DCB5678</serial-number>
      </device-inventory>
      <device-system-data>
        <software-version>Cisco IOS XE Software, Version 17.09.04a</software-version>
        <boot-time>2026-11-01T08:00:00+00:00</boot-time>
      </device-system-data>
    </device-hardware>
  </device-hardware-data>
</data>
"""


def test_native_and_system_data() -> None:
    """Hostname, version and the system leaves are returned with snake_case keys."""
    facts = system_facts(_REPLY)
    assert facts["hostname"] == "sw1"
    assert facts["version"] == "17.9"
    system = facts["system"]
    assert isinstance(system, dict)
    assert system["software_version"].startswith("Cisco IOS XE")
    assert system["boot_time"] == "2026-11-01T08:00:00+00:00"


def test_inventory_entries() -> None:
    """Every device-inventory entry becomes one dict."""
    inventory = system_facts(_REPLY)["inventory"]
    assert isinstance(inventory, list)
    assert [entry["serial_number"] for entry in inventory] == ["FCW1234", "DCB5678"]
    assert inventory[0]["part_number"] == "C9300-24P"
    assert inventory[0]["hw_dev_index"] == "0"


def test_missing_data_gives_empty_facts() -> None:
    """A reply without hardware data yields empty system and inventory."""
    facts = system_facts('<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"/>')
    assert facts == {"hostname": None, "version": None, "system": {}, "inventory": []}


def test_invalid_xml_raises_filter_error() -> None:
    """Broken XML is reported as AnsibleFilterError."""
    with pytest.raises(AnsibleFilterError):
        system_facts("<data>")
