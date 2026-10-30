---
name: draft-replies
description: Draft replies to EmailOps emails with emailops-cli and save them as drafts for the user to review and send from the app. Use when the user asks an agent to prepare, write or draft answers to one or more emails. Never sends.
---

# Draft replies with emailops-cli

The drafts land in the account's Drafts folder (and the provider's, for Gmail and
Outlook), where the user reviews and sends them from EmailOps. **Never pass `--send`.**
If the user asks you to send, tell them to send the draft from the app.

## Before you start

1. Run `emailops-cli doctor --json`. If it fails or `emailops-cli` is not on the PATH,
   tell the user how to install it (the EmailOps CLI guide: the `EmailOps-CLI-macos.dmg`
   release asset) and stop.
2. Every command below takes `--json` and prints one envelope:
   `{"ok": true, "data": …, "error": null}` or `{"ok": false, "data": null, "error": {"code", "message"}}`.
   Read `data`; on `ok: false`, report `error.message` and stop.
3. With several accounts, pass `--account <email>` to every command.

## For each email to answer

1. Read it: `emailops-cli show <id> --json`. Use `data.senderEmail`, `data.subject`,
   `data.cc` and `data.body`.
2. Write the reply:
   - Answer what was asked, in the language of the email, in the user's register (look
     at their sent mail with `emailops-cli emails --mailbox sent --limit 5 --json` once
     per session if you need it).
   - Short: a greeting, the answer, a next step if any, a sign-off. No invented facts,
     dates, prices or commitments. When the answer needs something only the user knows,
     leave a clear `[to fill: …]` marker and say so.
3. Save it as a draft, writing the body to a temporary file first so quotes and line
   breaks survive the shell:

   ```bash
   emailops-cli compose --to <senderEmail> --subject "Re: <subject>" \
     --body-file /tmp/reply.txt --json
   ```

   Add `--cc <address>` once per address the user wants copied. Keep the `Re:` prefix
   once: do not add it to a subject that already starts with it.
4. Delete the temporary file.

`compose` starts a new message: it is not attached to the original thread. Say so when
you hand the drafts over, so the user knows the reply will show as a new conversation.

## Report back

One line per draft: recipient, subject and the draft `id` from `data`, plus any
`[to fill: …]` markers left in it. To review one: `emailops-cli draft <id> --json`.
To discard one: `emailops-cli draft <id> --delete --json`. Never paste the user's mail
into files outside the temporary body file, commits or anything else.
