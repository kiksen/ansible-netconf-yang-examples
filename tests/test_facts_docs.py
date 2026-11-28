"""Check that every fact set by a facts role is documented in its argument_specs.yml."""

from pathlib import Path

import pytest
import yaml

ROLES = sorted(Path(__file__).parents[1].glob("roles/netconf/*/facts"))


def _set_facts(tasks: list[dict[str, object]]) -> set[str]:
    """Return the variable names that the tasks set with set_fact."""
    names: set[str] = set()
    for task in tasks:
        facts = task.get("ansible.builtin.set_fact")
        if isinstance(facts, dict):
            names.update(facts)
    return names


@pytest.mark.parametrize("role", ROLES, ids=lambda path: path.parent.name)
def test_return_values_documented(role: Path) -> None:
    """Every set_fact variable appears in the description of the argument spec."""
    tasks = yaml.safe_load((role / "tasks/main.yml").read_text())
    spec = yaml.safe_load((role / "meta/argument_specs.yml").read_text())
    description = " ".join(spec["argument_specs"]["main"]["description"])
    missing = {name for name in _set_facts(tasks) if f"{name} (" not in description}
    assert not missing
