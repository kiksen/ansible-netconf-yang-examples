"""Tests for the NetBox dynamic inventory script."""

import pytest
from netbox_switch import build_inventory, primary_address


def test_primary_address_strips_prefix() -> None:
    """The prefix length is removed from the primary IPv4 address."""
    assert (
        primary_address({"name": "sw", "primary_ip4": {"address": "10.10.10.144/24"}})
        == "10.10.10.144"
    )


def test_primary_address_missing() -> None:
    """A device without primary IP is an error."""
    with pytest.raises(ValueError, match="no primary IP"):
        primary_address({"name": "sw", "primary_ip4": None})


def test_build_inventory_host_vars() -> None:
    """The inventory has one host with the NETCONF connection variables."""
    inventory = build_inventory(
        {"name": "homidomi", "primary_ip4": {"address": "10.10.10.144/24"}}
    )
    host_vars = inventory["_meta"]["hostvars"]["switch"]
    assert host_vars["ansible_host"] == "10.10.10.144"
    assert host_vars["ansible_connection"] == "ansible.netcommon.netconf"
    assert host_vars["netbox_device"] == "homidomi"
    assert inventory["switches"]["hosts"] == ["switch"]
