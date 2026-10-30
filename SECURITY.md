# Security policy

A skill is a set of instructions an AI follows with access to someone's mail. A skill that
tells it to send mail, forward messages, leak their content into a draft or a link, or
ignore the user is a security problem, even though nothing in it is code.

## Reporting a harmful skill

Report it privately. **Do not open a public issue.**

Open a [private security advisory](https://github.com/emailops/emailops-skills/security/advisories/new)
on GitHub. It reaches the maintainers only and stays private until the skill is fixed or
removed.

Please include:

- The skill's folder, and the commit or release you looked at.
- What the instructions make the AI do, and the request that triggers it.
- The model or agent you saw it with, if you ran it.

Never attach mail from a real inbox. Describe what happened with made-up names instead.

We aim to acknowledge a report within **3 business days**.

## When a skill is withdrawn

A skill that can cause harm is removed from `main` first and fixed afterwards. We raise the
plugin's version and publish an advisory that names the skill and what it did.

Removing it from this repo does not remove it from your machine:

- **App skills** are your own copies. Delete the skill in the **Skills** view.
- **Hermes** keeps an installed skill. Remove it with `hermes skills uninstall <name>`.
- **Claude Code** keeps the installed version of the plugin until you run
  `claude plugin update emailops@emailops-skills`.

## Scope

In scope: the skills in `app-skills/` and `agent-skills/`, the plugin and marketplace
files, and `scripts/`.

Out of scope: the EmailOps app and `emailops-cli` themselves. Report those through the
[EmailOps security policy](https://github.com/emailops/emailops/security/policy).
