#!/usr/bin/env python3
"""Minimal dynamic inventory: one NETCONF switch whose address comes from NetBox.

Environment:
    NETBOX_ENDPOINT  NetBox base URL (required)
    NETBOX_TOKEN     NetBox API token, read-only is enough (required)
    NETBOX_DEVICE    NetBox device name (default: homidomi)

The host is called ``switch`` and gets ``ansible_host`` from the primary IPv4
address of the device. Connection settings are the lab defaults.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_DEVICE = "homidomi"
HOST_NAME = "switch"
CONNECTION_VARS: dict[str, Any] = {
    "ansible_port": 830,
    "ansible_user": "test",
    "ansible_password": "test",
    "ansible_connection": "ansible.netcommon.netconf",
    "ansible_network_os": "cisco.ios.ios",
    "ansible_netconf_host_key_checking": False,
}


def primary_address(device: dict[str, Any]) -> str:
    """Return the primary IPv4 address of a NetBox device without the prefix length."""
    primary = device.get("primary_ip4") or device.get("primary_ip")
    if not primary:
        raise ValueError(f"device {device.get('name')} has no primary IP in NetBox")
    return str(primary["address"]).split("/", 1)[0]


def build_inventory(device: dict[str, Any]) -> dict[str, Any]:
    """Build the Ansible inventory JSON structure for one NetBox device."""
    host_vars = {
        **CONNECTION_VARS,
        "ansible_host": primary_address(device),
        "netbox_device": device["name"],
    }
    return {
        "all": {"children": ["switches"]},
        "switches": {"hosts": [HOST_NAME]},
        "_meta": {"hostvars": {HOST_NAME: host_vars}},
    }


def fetch_device(endpoint: str, token: str, name: str) -> dict[str, Any]:
    """Read a single device by name from the NetBox REST API."""
    query = urllib.parse.urlencode({"name": name})
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/api/dcim/devices/?{query}",
        headers={"Authorization": f"Token {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.load(response)
    if payload["count"] != 1:
        raise LookupError(
            f"expected one NetBox device named {name}, got {payload['count']}"
        )
    result: dict[str, Any] = payload["results"][0]
    return result


def main() -> int:
    """Entry point implementing the --list / --host inventory script protocol."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--host")
    args = parser.parse_args()
    if args.host:
        print(json.dumps({}))
        return 0
    try:
        device = fetch_device(
            os.environ["NETBOX_ENDPOINT"],
            os.environ["NETBOX_TOKEN"],
            os.environ.get("NETBOX_DEVICE", DEFAULT_DEVICE),
        )
        print(json.dumps(build_inventory(device)))
    except (KeyError, LookupError, ValueError, OSError) as err:
        print(f"netbox_switch inventory failed: {err!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
