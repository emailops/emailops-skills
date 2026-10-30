---
name: triage-inbox
description: Triage the user's EmailOps inbox from the terminal with emailops-cli and rank what needs an answer first. Use when the user asks an agent what is waiting in their mail, what to answer first, or for an inbox review, and EmailOps is installed.
---

# Triage the inbox with emailops-cli

`emailops-cli` reads the mail the EmailOps app already synced, on this machine. These
steps only read: they never change, move or send anything.

## Before you start

1. Run `emailops-cli doctor --json`. If it fails or `emailops-cli` is not on the PATH,
   tell the user how to install it (the EmailOps CLI guide: the `EmailOps-CLI-macos.dmg`
   release asset) and stop.
2. Every command below takes `--json` and prints one envelope:
   `{"ok": true, "data": …, "error": null}` or `{"ok": false, "data": null, "error": {"code", "message"}}`.
   Read `data`; on `ok: false`, report `error.message` and stop. Exit code 3 means not
   found, 4 an auth problem, 5 a sync or network problem.
3. With more than one account, run `emailops-cli accounts --json` and pass
   `--account <email>` to every command, or ask the user which account to use.

## Steps

1. List recent inbox mail:
   `emailops-cli emails --mailbox inbox --limit 50 --json`.
   Each item has `id`, `threadId`, `sender`, `senderEmail`, `subject`, `snippet`,
   `timestamp` (Unix seconds) and `isRead`.
2. Group items by `threadId` and keep the newest message of each thread.
3. For a thread whose snippet does not make the ask clear, read it:
   `emailops-cli show <id> --json` (the body is in `data.body`). Read at most 5.
4. When the user names a topic or a sender, use
   `emailops-cli search "<words>" --limit 25 --json` instead of step 1.

## How to rank

- **Act today**: a decision, approval, payment, document or date is being asked for,
  or a deadline falls within 2 days.
- **This week**: a reply is expected but can wait a day or two.
- **Read later**: newsletters, notifications, receipts and FYI mail.

Unread before read, then older first.

## Answer

Three short sections in that order, one line per thread: sender, what they need, how
long ago, and the email `id` so the user can run `emailops-cli show <id>`. Give
**Read later** as a count. Never print whole email bodies back, and never paste mail
content into files, commits or anything outside this conversation.
