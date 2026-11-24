"""Mini-Client: rendert access_port.xml.j2 und schreibt es per NETCONF auf den Switch.

Start: uv run python pyclient/client.py
Bei einem Fehler wird die komplette rpc-error-Antwort des Switches ausgegeben.
"""

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from ncclient import manager
from ncclient.operations import RPCError

HOST = "10.10.10.144"
PORT = 830
USER = "test"
PASSWORD = "test"

# Variablen der Rolle netconf/port/access
PARAMS: dict[str, object] = {
    "port_access_interface": "GigabitEthernet1/0/5",
    "port_access_vlan": 123,
    "port_access_voice_vlan": None,
    "port_access_description": "Drucker",
    "port_access_no_cdp_enable": True,
    "port_access_no_lldp_transmit": True,
    "port_access_no_lldp_receive": True,
}

_INTERFACE_RE = re.compile(r"^(?P<type>[A-Za-z][A-Za-z-]*?)\s*(?P<id>\d+(?:/\d+)*)$")


def interface_part(name: str, part: str) -> str:
    """Minimal-Version des Ansible-Filters: liefert 'type' oder 'id' des Interface-Namens."""
    match = _INTERFACE_RE.match(name.strip())
    if match is None:
        raise ValueError(f"Ungueltiger Interface-Name: {name!r}")
    return match[part]


def render() -> str:
    """Rendert das Template mit PARAMS."""
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent),
        undefined=StrictUndefined,
    )
    env.filters["interface_part"] = interface_part
    return env.get_template("access_port.xml.j2").render(PARAMS)


def main() -> None:
    """Schreibt die gerenderte Konfiguration und zeigt Erfolg oder Fehlerdetails."""
    payload = render()
    print(payload)
    with manager.connect(
        host=HOST,
        port=PORT,
        username=USER,
        password=PASSWORD,
        hostkey_verify=False,
        look_for_keys=False,
        allow_agent=False,
        timeout=120,
    ) as session:
        try:
            reply = session.edit_config(target="running", config=payload)
        except RPCError as err:
            print("FEHLER:", err.type, err.tag, err.severity)
            print("Meldung:", err.message)
            print("Details:", err.info)
            return
        print("OK:", reply.ok)


if __name__ == "__main__":
    main()
