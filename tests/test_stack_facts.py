"""Tests for the filter stack_facts."""

import pytest
from ansible.errors import AnsibleFilterError
from stack_facts import stack_facts

# Hand-written reply following CISCO-STACKWISE-MIB; the real field set comes from the device.
_REPLY = """
<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <CISCO-STACKWISE-MIB xmlns="urn:ietf:params:xml:ns:yang:smiv2:CISCO-STACKWISE-MIB">
    <cswGlobals>
      <cswMaxSwitchNum>9</cswMaxSwitchNum>
    </cswGlobals>
    <cswSwitchInfoTable>
      <cswSwitchInfoEntry>
        <cswSwitchNumCurrent>1</cswSwitchNumCurrent>
        <cswSwitchRole>master</cswSwitchRole>
        <cswSwitchSwPriority>15</cswSwitchSwPriority>
        <cswSwitchState>ready</cswSwitchState>
      </cswSwitchInfoEntry>
      <cswSwitchInfoEntry>
        <cswSwitchNumCurrent>2</cswSwitchNumCurrent>
        <cswSwitchRole>member</cswSwitchRole>
        <cswSwitchSwPriority>1</cswSwitchSwPriority>
        <cswSwitchState>ready</cswSwitchState>
      </cswSwitchInfoEntry>
    </cswSwitchInfoTable>
  </CISCO-STACKWISE-MIB>
</data>
"""


def test_members_are_the_switch_info_entries() -> None:
    """One member dict per cswSwitchInfoEntry."""
    members = stack_facts(_REPLY)["members"]
    assert isinstance(members, list)
    assert [m["cswSwitchNumCurrent"] for m in members] == ["1", "2"]
    assert members[0]["cswSwitchRole"] == "master"


def test_globals_and_tables() -> None:
    """Plain containers end up in globals, entry lists in tables."""
    facts = stack_facts(_REPLY)
    assert facts["globals"] == {"cswMaxSwitchNum": "9"}
    tables = facts["tables"]
    assert isinstance(tables, dict)
    assert list(tables) == ["cswSwitchInfoTable"]


def test_empty_reply_gives_empty_facts() -> None:
    """A reply without the module (no stack data) yields empty facts."""
    facts = stack_facts('<data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"/>')
    assert facts == {"globals": {}, "tables": {}, "members": []}


def test_invalid_xml_raises_filter_error() -> None:
    """Broken XML is reported as AnsibleFilterError."""
    with pytest.raises(AnsibleFilterError):
        stack_facts("<data>")
