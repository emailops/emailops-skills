"""The plugin version check: a change under agent-skills/ must raise the plugin's version."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from check_version import version_problem  # noqa: E402

SKILL = "agent-skills/skills/triage-inbox/SKILL.md"


def test_a_changed_agent_skill_with_a_raised_version_passes():
    assert version_problem([SKILL], "0.1.0", "0.2.0") is None


def test_a_changed_agent_skill_with_the_same_version_fails():
    assert "0.1.0" in version_problem([SKILL], "0.1.0", "0.1.0")


def test_a_lowered_version_fails():
    assert version_problem([SKILL], "0.2.0", "0.1.9") is not None


def test_versions_compare_as_numbers_not_text():
    assert version_problem([SKILL], "0.9.0", "0.10.0") is None


def test_changes_outside_agent_skills_need_no_new_version():
    assert version_problem(["app-skills/inbox-triage/SKILL.md", "README.md"], "0.1.0", "0.1.0") is None


def test_a_version_that_is_not_three_numbers_fails():
    assert "1.0" in version_problem([SKILL], "0.1.0", "1.0")
