#!/usr/bin/env python3
"""Fail when a change under agent-skills/ keeps the plugin's version.

  python3 scripts/check_version.py BASE_REF

Claude Code decides whether an installed plugin has an update by comparing the
`version` in agent-skills/.claude-plugin/plugin.json, so a skill edited without
raising it never reaches the people who already installed the plugin. Compares
the working tree against BASE_REF (the pull request's target branch in CI).
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

PLUGIN_DIR = "agent-skills/"
PLUGIN_JSON = "agent-skills/.claude-plugin/plugin.json"
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def version_problem(changed, base_version, head_version):
    """Why the plugin's version is wrong for these changed paths, or None. Pure."""
    if not any(path.startswith(PLUGIN_DIR) for path in changed):
        return None
    match = VERSION.match(head_version)
    if not match:
        return f"{PLUGIN_JSON}: version {head_version!r} is not three numbers like 0.2.0"
    base = VERSION.match(base_version)
    if base and tuple(map(int, match.groups())) <= tuple(map(int, base.groups())):
        return f"{PLUGIN_JSON}: agent skills changed, so raise the version above {base_version} (it is {head_version})"
    return None


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    base_ref = argv[1]
    changed = git("diff", "--name-only", f"{base_ref}...HEAD").split()
    base_version = json.loads(git("show", f"{base_ref}:{PLUGIN_JSON}"))["version"]
    head_version = json.loads(pathlib.Path(PLUGIN_JSON).read_text(encoding="utf-8"))["version"]
    problem = version_problem(changed, base_version, head_version)
    print(problem or f"plugin version {head_version}: ok")
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
