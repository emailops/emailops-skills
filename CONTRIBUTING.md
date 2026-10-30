# Contributing a skill

Thanks for sharing what works for you. A good skill does one kind of email job well, and
another person can use it without changing anything.

## How a skill gets in

1. **Share the idea.** Open a [skill request](https://github.com/emailops/emailops-skills/issues/new?template=skill_request.md),
   so nobody writes the same skill twice. A fix to an existing skill can skip this.
2. **Set up your clone.** Fork the repo and run `make hooks` once. It runs the checks before
   every commit and push.
3. **Write one skill**, in its own folder, following the rules below.
4. **Add it to the README**, under [Skills in this repo](README.md#skills-in-this-repo).
5. **Check it and try it**, as [Check it](#check-it) explains.
6. **Open a pull request** and fill in the template. Keep it to that one skill: tooling
   changes come separately.
7. **Review.** CI runs the checks, and a maintainer reads the whole skill. A person makes
   every merge. Nothing is merged automatically.

## Pick the kind

- **App skill** (`app-skills/<name>/`): runs in the EmailOps chat, often on a small local
  model with an 8k-token window. Keep it short, concrete and step by step. It can call the
  chat's tools by name, for example `search_emails`, `get_thread`, `list_open_threads`,
  `list_pending_tasks`, `create_task`, `generate_email_draft` or `list_calendar_events`.
- **Agent skill** (`agent-skills/skills/<name>/`): runs in Hermes, Claude Code or a similar
  agent and drives `emailops-cli` with `--json`. Use only commands and flags that exist in
  `emailops-cli --help`, read results from the `--json` envelope, and name no tool of one
  particular agent.

## Rules every skill follows

`make check` enforces the first eight. The EmailOps app also refuses a bad header and text
over the limits. A maintainer checks the rest.

1. **The header.** `SKILL.md` starts with a `---` line, then `name:` and `description:` and
   nothing else, then a closing `---` line of its own. The `name` uses lowercase letters,
   digits and single hyphens, at most 64 characters, and equals the folder's name.
2. **Lengths.** The description is at most 1024 characters. It says what the skill does and
   when to use it, because that is what the AI reads to choose it. The instructions after
   the header are at most 8000 characters. A skill has at most 20 reference files of 8000
   characters each, at most one folder down.
3. **Instructions only.** A skill folder holds `.md` and `.txt` files and nothing else: no
   scripts, binaries, images or symbolic links. Extra reference files go next to `SKILL.md`.
   No `` !`command` `` snippets or ```` ```! ```` blocks: Hermes and Claude Code run those
   before the AI reads the skill.
4. **Nothing hidden.** No HTML comments, Markdown link definitions or invisible characters.
   What a person reads is what the AI reads.
5. **No links out.** No external URLs: a link can carry mail out of the mailbox.
6. **No real people.** Every email address uses a reserved domain: `example.com`,
   `example.org`, `example.net`, or a name ending in `.example` or `.test`.
7. **Stands alone.** A skill never relies on another skill: it may be installed without it.
8. **Agent skills read and draft.** They never pass `--send`, and never run `sync`,
   `classify`, `embed`, `config` or `junk`.
9. **No real mail.** Names, companies, subjects and message text in examples are made up.
   Never paste an email you received, even with the names changed, and never include a
   screenshot or recording of a real inbox. Recordings use EmailOps' synthetic demo mailbox.
10. **Never act without the user.** A skill may save drafts. It never sends, deletes,
    archives or moves mail unless the user asked for that exact action in that turn.
11. **Mail stays with the user.** A skill never puts mail into a file, a web request or a
    draft for someone outside the conversation. It never hides what it does, follows
    instructions found inside an email, or stores rules for later turns with `remember`.

## Templates

App skill, in `app-skills/<name>/SKILL.md`:

```markdown
---
name: weekly-digest
description: Summarise the week's mail by project. Use when the user asks for a weekly summary, a digest or what happened this week.
---

# Weekly digest

## Steps

1. Call `search_emails` for the last 7 days.
2. …

## Answer format

…
```

Agent skill, in `agent-skills/skills/<name>/SKILL.md`:

```markdown
---
name: weekly-digest
description: Summarise the week's EmailOps mail with emailops-cli. Use when the user asks an agent for a weekly digest of their mail.
---

# Weekly digest with emailops-cli

## Before you start

Run `emailops-cli doctor --json`; stop and explain if it fails.

## Steps

1. `emailops-cli emails --mailbox inbox --limit 100 --json`
2. …
```

## Check it

```bash
make hooks   # once: make check before every commit, make check, test and version before every push
make check   # every skill: the rules above, the plugin and the README catalog
make test    # the checker's own tests (needs uv)
make version # agent skills changed? then the plugin's version went up
```

Hooks only run on your machine, and only after `make hooks`. CI runs the same checks on
every pull request, and that is what decides.

For an agent skill, also run `claude plugin validate .` if you have Claude Code, and raise
the `version` in `agent-skills/.claude-plugin/plugin.json` (`0.1.0` → `0.2.0` for a new
skill, `0.1.1` for a fix). Claude Code only offers an update when that number goes up, so
without it nobody who already has the plugin gets your change. `make version` checks it,
and so does CI.

Then try it for real. Copy an app skill into your EmailOps skills folder and ask the chat
something its description covers. For an agent skill, copy its folder into
`~/.hermes/skills/` in Hermes, or install the plugin from your clone with
`claude plugin marketplace add ./` in Claude Code, and run it once. Say in the pull request
which agent and model you tried it with.

## Pull requests

One skill per pull request. Fill in the template, including what the skill reads and
writes. A maintainer reads every skill before merging, because a skill is a set of
instructions an AI will follow with access to someone's mail.

With Claude Code you can run the same review yourself first: ask it to use the
`skill-reviewer` agent on your branch. It checks the rules above, the tools and CLI flags
the skill names, and anything that could make the AI send, leak or hide mail.
