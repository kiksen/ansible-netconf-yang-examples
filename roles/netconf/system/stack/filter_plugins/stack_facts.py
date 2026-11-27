"""Jinja filter that turns a CISCO-STACKWISE-MIB reply into stack facts."""

from ansible.errors import AnsibleFilterError
from lxml import etree
from lxml.etree import _Element as Element

# Table that holds one entry per stack member (switch number, role, priority, state, MAC).
MEMBER_TABLE = "cswSwitchInfoTable"


def _local(element: Element) -> str:
    """Return the tag name of an element without its namespace."""
    return etree.QName(element).localname


def _leaves(parent: Element) -> dict[str, str | None]:
    """Return the leaf children of ``parent`` as dict; a leaf without text is None."""
    return {
        _local(child): (child.text or "").strip() or None
        for child in parent
        if len(child) == 0
    }


def parse_stack_facts(xml: str) -> dict[str, object]:
    """Parse a get reply of CISCO-STACKWISE-MIB into globals, tables and members.

    A direct child of the module container is a table when all of its children
    have children themselves (one entry each); otherwise it is a container of
    plain values and ends up in ``globals``.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(xml.encode(), parser)
    module = root.find(".//{*}CISCO-STACKWISE-MIB")
    values: dict[str, str | None] = {}
    tables: dict[str, list[dict[str, str | None]]] = {}
    if module is not None:
        for child in module:
            if len(child) == 0:
                values[_local(child)] = (child.text or "").strip() or None
            elif all(len(entry) > 0 for entry in child):
                tables[_local(child)] = [_leaves(entry) for entry in child]
            else:
                values.update(_leaves(child))
    return {
        "globals": values,
        "tables": tables,
        "members": tables.get(MEMBER_TABLE, []),
    }


def stack_facts(xml: str) -> dict[str, object]:
    """Jinja filter: return globals, tables and members of a CISCO-STACKWISE-MIB reply.

    Keys keep the MIB names (e.g. ``cswSwitchRole``). ``members`` is the list of
    entries of ``cswSwitchInfoTable``, one per stack member. Example:
    ``reply.stdout | stack_facts``.
    """
    try:
        return parse_stack_facts(str(xml))
    except etree.XMLSyntaxError as err:
        raise AnsibleFilterError(f"stack_facts: {err}") from err


class FilterModule:
    """Register the filter with Ansible."""

    def filters(self) -> dict[str, object]:
        """Return the available filters."""
        return {"stack_facts": stack_facts}
