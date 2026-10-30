#!/usr/bin/env python3
"""Check every skill in the repo the way the EmailOps app loads one, plus the repo's own rules.

  python3 scripts/check.py [ROOT]

A skill is a folder holding a SKILL.md: frontmatter with `name` (equal to the
folder) and `description`, then Markdown instructions. The limits are the app's
(src-tauri/src/services/skills in the EmailOps repo): a name of lowercase
letters, digits and single hyphens up to 64 characters, a description up to
1024 and instructions up to 8000.

On top of that, the repo's own rules. Skills are text a person can read in
full, and the app never runs them, but Hermes and Claude Code can run shell
from a skill's text and a Claude Code plugin can ship hooks, servers and
binaries. So a skill folder holds only .md and .txt files, with no shell
snippets, hidden text or external links, and only `name` and `description` in
its header. Every email address uses a reserved example domain. The plugin is
its manifest and its skills, and each skill stands alone and is in the README.
Exits 1 when anything fails. No dependencies beyond Python 3.9.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import unicodedata
from urllib.parse import urlsplit

MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024
MAX_BODY_CHARS = 8000
# The app lists this many reference files, at most one folder down.
MAX_REFERENCE_FILES = 20
MAX_REFERENCE_PARTS = 2
SKILL_FILE = "SKILL.md"
ALLOWED_SUFFIXES = {".md", ".txt"}
ALLOWED_FIELDS = ("name", "description")
# Where skills live: the app's chat skills, and the Claude Code plugin's skills.
APP_SKILLS = "app-skills"
AGENT_SKILLS = "agent-skills/skills"
PLUGIN_DIR = "agent-skills"
PLUGIN_JSON = "agent-skills/.claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
# Everything else a manifest can declare is a component, and components run.
ALLOWED_PLUGIN_KEYS = ("name", "description", "version", "license", "author")
ALLOWED_ENTRY_KEYS = ("name", "source", "description")
PLUGIN_SOURCE = "./agent-skills"
# Commands that change mail, models or settings, for the user to run themselves.
FORBIDDEN_COMMANDS = ("sync", "classify", "embed", "config", "junk")
# RFC 2606 / RFC 6761 names that never belong to anyone.
RESERVED_DOMAINS = ("example.com", "example.org", "example.net")
RESERVED_TLDS = ("example", "test", "invalid", "localhost")
ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})")
KEY_VALUE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$")
# Hermes and Claude Code run !`cmd` and ```! blocks before the model reads the skill.
SHELL_SNIPPET = re.compile(r"(?:^|\s)!`|^\s*(?:`{3,}|~{3,})\s*!", re.MULTILINE)
# Markdown renders neither of these, so a reader of the page never sees them.
HTML_COMMENT = "<!--"
LINK_DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:\s", re.MULTILINE)
LINK = re.compile(r"""\b[a-z][a-z0-9+.-]*://[^\s)>\]"'`]+|\bwww\.[^\s)>\]"'`]+|\bdata:[a-z]+/[^\s)>\]"'`]*""", re.IGNORECASE)
WORKFLOWS = ".github/workflows"
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)", re.MULTILINE)
PINNED_ACTION = re.compile(r"@[0-9a-f]{40}$")
CLI_SEND = re.compile(r"emailops-cli[^\n]*--send\b")
CLI_FORBIDDEN = re.compile(rf"emailops-cli(?:\s+--?\S+(?:\s+[^-\s]\S*)?)*?\s+({'|'.join(FORBIDDEN_COMMANDS)})\b")


def read_frontmatter(text):
    """(fields, body) of a SKILL.md: the YAML subset skills use (`key: value`, quoted values, > or | blocks). Pure."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter: the file must start with a --- line")
    rest = text[4:]
    end = rest.find("\n---")
    if end == -1:
        raise ValueError("the frontmatter is never closed with a --- line")
    after = rest[end + 4 :]
    newline = after.find("\n")
    if after[: newline if newline != -1 else len(after)].strip():
        raise ValueError("the closing --- must be on a line of its own")
    body = after[newline + 1 :] if newline != -1 else ""
    return parse_fields(rest[:end].split("\n")), body


def parse_fields(lines):
    fields, key = {}, None
    for number, line in enumerate(lines, 1):
        if key is not None and (line.startswith((" ", "\t")) or not line.strip()):
            fields[key] += " " + line.strip()  # a > or | block; the app collapses the whitespace anyway
            continue
        key = None
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = KEY_VALUE.match(line)
        if match is None:
            raise ValueError(f"frontmatter line {number} is not `key: value`: {line}")
        name, value = match.group(1), match.group(2).strip()
        if value in (">", "|", ">-", "|-"):
            fields[name], key = "", name
        else:
            fields[name] = unquote(value)
    return fields


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def valid_name(name):
    return (
        len(name) <= MAX_NAME_CHARS
        and not name.startswith("-")
        and not name.endswith("-")
        and "--" not in name
        and all(c.islower() and c.isascii() or c.isdigit() or c == "-" for c in name)
    )


def parse_skill_md(text, folder):
    """(name, description, body) of a SKILL.md in folder, or ValueError with the reason the app would give. Pure."""
    fields, body = read_frontmatter(text)
    name = fields.get("name", "").strip()
    if not name:
        raise ValueError("no name")
    if not valid_name(name):
        raise ValueError(f"`{name}` is not a valid skill name: use lowercase letters, digits and single hyphens, at most {MAX_NAME_CHARS} characters")
    if name != folder:
        raise ValueError(f"the name `{name}` does not match its folder `{folder}`")
    description = " ".join(fields.get("description", "").split())
    if not description:
        raise ValueError("no description")
    if len(description) > MAX_DESCRIPTION_CHARS:
        raise ValueError(f"the description is longer than {MAX_DESCRIPTION_CHARS} characters")
    body = body.strip()
    if not body:
        raise ValueError("no instructions after the frontmatter")
    if len(body) > MAX_BODY_CHARS:
        raise ValueError(f"the instructions are longer than {MAX_BODY_CHARS} characters")
    return name, description, body


def reserved(domain):
    domain = domain.lower()
    return any(domain == d or domain.endswith("." + d) for d in RESERVED_DOMAINS) or domain.rsplit(".", 1)[-1] in RESERVED_TLDS


def real_addresses(text):
    """Every email address in text whose domain is not a reserved example one. Pure."""
    return [m.group(0) for m in ADDRESS.finditer(text) if not reserved(m.group(1))]


def extra_fields(text):
    """The header keys beyond `name` and `description`. Pure."""
    return [key for key in read_frontmatter(text)[0] if key not in ALLOWED_FIELDS]


def invisible(char):
    """A character that shows nothing, or something else, in a diff or on a page. Pure."""
    if char in "\n\r\t":
        return False
    code = ord(char)
    return unicodedata.category(char) in ("Cc", "Cf", "Cn", "Co", "Cs", "Zl", "Zp") or 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF


def external(link):
    """Whether a link leaves the reserved example names. Pure."""
    try:
        host = urlsplit(link if "://" in link else f"//{link}").hostname
    except ValueError:
        return True
    return host is None or not reserved(host)


def text_problems(text, agent):
    """Why this text cannot be in a skill: what could run, hide or leak. Pure."""
    problems = []
    if SHELL_SNIPPET.search(text):
        problems.append("shell snippet: Hermes and Claude Code run these, and nothing in a skill may run")
    if HTML_COMMENT in text:
        problems.append("HTML comment: a reader of the page cannot see it, and the AI can")
    if LINK_DEFINITION.search(text):
        problems.append("link definition: a reader of the page cannot see it, and the AI can")
    hidden = sorted({c for c in text.removeprefix("\ufeff") if invisible(c)})
    if hidden:
        problems.append(f"invisible characters {', '.join(f'U+{ord(c):04X}' for c in hidden)}")
    problems += [f"external link {link}: a link can carry mail out of the mailbox" for link in LINK.findall(text) if external(link)]
    if agent:
        joined = text.replace("\\\n", " ")
        if CLI_SEND.search(joined):
            problems.append("emailops-cli with --send: an agent skill saves drafts and never sends")
        problems += [f"emailops-cli `{command}`: an agent skill never changes mail or settings" for command in CLI_FORBIDDEN.findall(joined)]
    return problems


def check_folder(folder, agent=False):
    """The problems of one skill folder, each as `path: reason`."""
    if folder.is_symlink():
        return [f"{folder}: symbolic links are not allowed in a skill"]
    skill_md = folder / SKILL_FILE
    if not skill_md.is_file():
        return [f"{folder}: no {SKILL_FILE}"]
    problems = []
    references = 0
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            problems.append(f"{path}: symbolic links are not allowed in a skill")
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f"{path}: only .md and .txt files are allowed in a skill (nothing in a skill is ever run)")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"{path}: not UTF-8 text")
            continue
        if path == skill_md:
            try:
                parse_skill_md(text, folder.name)
                problems += [f"{path}: the header may hold only `name` and `description`, not `{key}`" for key in extra_fields(text)]
            except ValueError as err:
                problems.append(f"{path}: {err}")
        else:
            references += 1
            if len(path.relative_to(folder).parts) > MAX_REFERENCE_PARTS:
                problems.append(f"{path}: too deep; the app reads a reference file at most one folder down")
            if len(text) > MAX_BODY_CHARS:
                problems.append(f"{path}: longer than {MAX_BODY_CHARS} characters; the app would cut it")
        problems += [f"{path}: real-looking address {a}; use a reserved domain such as example.com" for a in real_addresses(text)]
        problems += [f"{path}: {problem}" for problem in text_problems(text, agent)]
    if references > MAX_REFERENCE_FILES:
        problems.append(f"{folder}: {references} reference files; the app lists at most {MAX_REFERENCE_FILES}")
    return problems


def load_json(root, rel, problems):
    """The manifest at rel as a dict, or {} with the reason added to problems."""
    try:
        return json.loads((root / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        problems.append(f"{rel}: cannot read it: {err}")
        return {}


def plugin_problems(root):
    """What the plugin carries beyond its manifest and skills: anything else can run."""
    problems = []
    only = "the plugin may hold only .claude-plugin/plugin.json and skills/"
    plugin = root / PLUGIN_DIR
    for entry in sorted(plugin.iterdir()) if plugin.is_dir() else []:
        if entry.is_symlink() or entry.name not in (".claude-plugin", "skills"):
            problems.append(f"{PLUGIN_DIR}/{entry.name}: {only}")
    manifests = plugin / ".claude-plugin"
    for entry in sorted(manifests.iterdir()) if manifests.is_dir() else []:
        if entry.name != "plugin.json":
            problems.append(f"{PLUGIN_DIR}/.claude-plugin/{entry.name}: {only}")
    manifest = load_json(root, PLUGIN_JSON, problems)
    problems += [f"{PLUGIN_JSON}: `{key}` is not allowed; the plugin is metadata and skills" for key in manifest if key not in ALLOWED_PLUGIN_KEYS]
    entries = load_json(root, MARKETPLACE_JSON, problems).get("plugins", [])
    if len(entries) != 1 or entries[0].get("source") != PLUGIN_SOURCE:
        problems.append(f"{MARKETPLACE_JSON}: the marketplace lists exactly one plugin, `{PLUGIN_SOURCE}`")
    problems += [f"{MARKETPLACE_JSON}: `{key}` is not allowed in the plugin entry" for entry in entries for key in entry if key not in ALLOWED_ENTRY_KEYS]
    return problems


def catalog_problems(root, folders):
    """The skills the README does not list."""
    readme = root / "README.md"
    listed = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    rels = [f.relative_to(root).as_posix() for f in folders]
    return [f"README.md: {rel}/{SKILL_FILE} is missing from the catalog" for rel in rels if f"{rel}/{SKILL_FILE}" not in listed]


def dependency_problems(folders):
    """Skills that send the reader to another skill, which may not be installed."""
    names = {f.name for f in folders}
    problems = []
    for folder in folders:
        skill_md = folder / SKILL_FILE
        if folder.is_symlink() or skill_md.is_symlink() or not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        problems += [f"{skill_md}: relies on the skill `{name}`; a skill may be installed alone" for name in sorted(names - {folder.name}) if f"`{name}`" in text]
    return problems


def workflow_problems(root):
    """Workflow lines that would let someone else's code run with more than a read-only token."""
    problems = []
    workflows = root / WORKFLOWS
    for path in sorted(workflows.glob("*.yml")) if workflows.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        rel = f"{WORKFLOWS}/{path.name}"
        if "pull_request_target" in text:
            problems.append(f"{rel}: pull_request_target runs a fork's code with this repo's secrets")
        problems += [f"{rel}: {action} must be pinned to a commit SHA" for action in USES.findall(text) if not PINNED_ACTION.search(action)]
    return problems


def check_repo(root):
    """(number of skills checked, problems) over every skill folder under root."""
    folders, problems = [], []
    for rel, agent in ((APP_SKILLS, False), (AGENT_SKILLS, True)):
        skills = root / rel
        for entry in sorted(skills.iterdir()) if skills.is_dir() else []:
            if entry.is_dir():
                folders.append(entry)
                problems += check_folder(entry, agent=agent)
            else:
                problems.append(f"{entry}: only skill folders belong here")
    return len(folders), problems + plugin_problems(root) + catalog_problems(root, folders) + dependency_problems(folders) + workflow_problems(root)


def main(argv):
    root = pathlib.Path(argv[1] if len(argv) > 1 else pathlib.Path(__file__).resolve().parent.parent)
    count, problems = check_repo(root)
    for problem in problems:
        print(problem)
    print(f"{count} skills, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
