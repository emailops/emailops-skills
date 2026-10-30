## What the skill does

<!-- One or two sentences: the email job it handles and when the AI should pick it. -->

## Kind

- [ ] App skill (`app-skills/`)
- [ ] Agent skill (`agent-skills/skills/`)

## What it reads and writes

- Reads: <!-- for example: inbox threads, sent mail, calendar -->
- Writes: <!-- for example: nothing, a draft, a task -->

## Checklist

- [ ] `make check` passes (run `make hooks` once to have it checked on every commit).
- [ ] The skill is in the README catalog and does not rely on another skill.
- [ ] Agent skill: I raised the version in `agent-skills/.claude-plugin/plugin.json` (`make version` passes).
- [ ] Every name, company, address, subject and message in it is made up; addresses use `example.com` or another reserved domain.
- [ ] It contains no email I received, even with the names changed, and no screenshots of a real inbox.
- [ ] It never sends, deletes, archives or moves mail on its own (no `--send` in agent skills).
- [ ] This pull request changes this one skill and nothing else in the repo's tooling.
- [ ] I tried it. Agent (the EmailOps chat, Hermes, Claude Code or other) and model:
