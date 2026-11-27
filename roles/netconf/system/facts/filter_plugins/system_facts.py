"""Jinja filter that turns a device-hardware-oper reply into system and inventory facts."""

from ansible.errors import AnsibleFilterError
from lxml import etree
from lxml.etree import _Element as Element


def _local(element: Element) -> str:
    """Return the tag name of an element without its namespace."""
    return etree.QName(element).localname


def _text(parent: Element | None, path: str) -> str | None:
    """Return the stripped text of the element at ``path`` below ``parent``."""
    if parent is None:
        return None
    found = parent.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip()


def _leaves(parent: Element) -> dict[str, str | None]:
    """Return the leaf children of ``parent`` as dict with snake_case keys.

    Child containers are skipped; a leaf without text (a presence flag) is None.
    """
    return {
        _local(child).replace("-", "_"): (child.text or "").strip() or None
        for child in parent
        if len(child) == 0
    }


def parse_system_facts(xml: str) -> dict[str, object]:
    """Parse a get reply into hostname, version, system data and inventory."""
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(xml.encode(), parser)
    system = root.find(
        ".//{*}device-hardware-data/{*}device-hardware/{*}device-system-data"
    )
    inventory = root.iterfind(
        ".//{*}device-hardware-data/{*}device-hardware/{*}device-inventory"
    )
    return {
        "hostname": _text(root, ".//{*}native/{*}hostname"),
        "version": _text(root, ".//{*}native/{*}version"),
        "system": _leaves(system) if system is not None else {},
        "inventory": [_leaves(entry) for entry in inventory],
    }


def system_facts(xml: str) -> dict[str, object]:
    """Jinja filter: return hostname, version, system and inventory facts of a reply.

    ``system`` holds the leaves of device-system-data (what ``show version``
    reports: software_version, boot_time, last_reboot_reason, ...). ``inventory``
    is a list with one dict per device-inventory entry (what ``show inventory``
    reports: hw_type, dev_name, hw_description, part_number, serial_number, ...).
    Example: ``reply.stdout | system_facts``.
    """
    try:
        return parse_system_facts(str(xml))
    except etree.XMLSyntaxError as err:
        raise AnsibleFilterError(f"system_facts: {err}") from err


class FilterModule:
    """Register the filter with Ansible."""

    def filters(self) -> dict[str, object]:
        """Return the available filters."""
        return {"system_facts": system_facts}
