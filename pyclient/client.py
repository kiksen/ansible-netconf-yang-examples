"""Mini client: renders access_port.xml.j2 and writes it to the switch via NETCONF.

Start: uv run python pyclient/client.py
On an error the complete rpc-error reply of the switch is printed.
"""

import re

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from lxml import etree
from ncclient import manager
from ncclient.manager import Manager
from ncclient.operations import RPCError

HOST: str = "10.10.10.144"
PORT: int = 830
USER: str = "test"
PASSWORD: str = "test"

# Variables of the role netconf/port/access
PARAMS: dict[str, object] = {
    "port_access_interface": "GigabitEthernet1/0/5",
    "port_access_vlan": 123,
    "port_access_voice_vlan": None,
    "port_access_description": "Drucker",
    "port_access_no_cdp_enable": True,
    "port_access_no_lldp_transmit": True,
    "port_access_no_lldp_receive": True,
    # Test flag only (not a role variable): True resets the interface in the same
    # edit-config via nc:operation="replace" (like "default interface"), False merges.
    "port_access_reset": True,
    # Problem elements removed before the write (only if present on the device).
    "port_access_cleanup_elements": [
        {"name": "rep", "namespace": "http://cisco.com/ns/yang/Cisco-IOS-XE-rep"},
    ],
}


def pretty(xml: str) -> str:
    """Return the XML string indented."""
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml.encode(), parser)
    return etree.tostring(root, pretty_print=True, encoding="unicode")


_INTERFACE_RE = re.compile(r"^(?P<type>[A-Za-z][A-Za-z-]*?)\s*(?P<id>\d+(?:/\d+)*)$")


def interface_part(name: str, part: str) -> str:
    """Return 'type' or 'id' of an interface name (minimal version of the Ansible filter)."""
    match = _INTERFACE_RE.match(name.strip())
    if match is None:
        raise ValueError(f"Invalid interface name: {name!r}")
    return match[part]


def render(template_name: str, **extra: object) -> str:
    """Render a template from pyclient/templates with PARAMS plus extra variables."""
    env = Environment(
        loader=FileSystemLoader("./pyclient/templates"),
        undefined=StrictUndefined,
    )
    env.filters["interface_part"] = interface_part
    return env.get_template(template_name).render(PARAMS | extra)


def get_running(session: manager.Manager, subtree: str) -> str:
    """Read the running config limited to the given subtree filter."""
    return session.get_config(source="running", filter=("subtree", subtree)).data_xml


def cleanup_present(running_xml: str) -> list[dict[str, str]]:
    """Return the cleanup elements whose namespace occurs in the running config."""
    elements: list[dict[str, str]] = PARAMS["port_access_cleanup_elements"]  # type: ignore[assignment]  # PARAMS is untyped
    return [element for element in elements if element["namespace"] in running_xml]


def open_session() -> Manager:
    return manager.connect(
        host=HOST,
        port=PORT,
        username=USER,
        password=PASSWORD,
        hostkey_verify=False,
        look_for_keys=False,
        allow_agent=False,
        timeout=120,
        device_params={"name": "iosxe"},
    )  # type: ignore[attr-defined]


def main() -> None:
    """Write the rendered config and report changed/unchanged or error details."""
    payload = render("access_port.xml.j2")
    get_filter = render("get_filter.xml.j2")
    print(payload)
    with open_session() as session:
        before = get_running(session, get_filter)
        present = cleanup_present(before)
        before = pretty(before)
        try:
            if present:
                cleaner = render("cleaner.xml.j2", port_access_cleanup_present=present)
                print(cleaner)
                session.edit_config(target="running", config=cleaner)
            reply = session.edit_config(target="running", config=payload)
            print(pretty(reply.xml))

        except RPCError as err:
            print("ERROR:", err.type, err.tag, err.severity)
            print("Message:", err.message)
            print("Details:", err.info)
            return
        after = get_running(session, get_filter)
        print("OK:", reply.ok)
        print("changed" if before != after else "unchanged")
        print(pretty(after))


if __name__ == "__main__":
    main()
