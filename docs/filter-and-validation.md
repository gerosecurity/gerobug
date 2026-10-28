# Filter & Validation

Is Gerobug secure? Nothing is 100% secure, but Gerobug filters and validates everything it receives by default.

## Accepted Email Format

Gerobug only processes emails whose subject matches a known command (`SUBMIT_`, `CHECK_`, `STATUS_OVERVIEW`, `UPDATE_`, `APPEAL_`, `AGREE_`, `DATA_`/`NDA_`, `MY_SCORE`). Anything else gets an "Invalid Report Format" reply. See the [Bug Hunter Guide](bug-hunter-guide.md) for the full format and limits.

## Sender Authentication

Gerobug never replies to or processes a message it cannot trust:

* **Spoofed senders.** If the receiving mail server adds an `Authentication-Results` header, a message whose **SPF and DKIM both fail** is dropped. Without that header, Gerobug falls back to comparing `Return-Path` with `From:` (case-insensitive).

{% hint style="warning" %}
The `Return-Path` fallback is not real authentication: a sender talking raw SMTP controls both headers. Run Gerobug behind a mail provider that stamps `Authentication-Results` (Gmail and Outlook do).
{% endhint %}

* **No-reply senders** are ignored.
* **Mail loops.** Gerobug ignores mail from its own address, from senders marked `Auto-Submitted` (auto-responders), and from other addresses on its own domain (unless the mailbox is on a free provider such as Gmail). Outgoing mail is marked `Auto-Submitted: auto-generated` and carries a proper `Message-ID`, so two Gerobug instances cannot ping-pong replies.
* **Bounces** (delivery status notifications) are detected, logged and sent to Slack/Telegram with the failed recipient, Report ID and SMTP error, instead of being processed as reports.

## File Validation

* Attachments must be valid PDFs. The file is checked in memory and is never written to disk if it is invalid.
* Attachments of 25 MB or more are rejected.
* Files are saved under a server-generated name (`<Report ID>.pdf`, `<Report ID>U1.pdf`, ...). Path traversal is blocked.
* Dashboard uploads (templates, logo, signature) are checked by magic bytes, extension and size.

What about malicious PDFs? Since submissions arrive through the mail provider, malicious attachments are usually filtered there first (risk transfer). Open hunter PDFs with care.

## User Authorization

A hunter can only check or act on reports sent from their own email address. `user1@email.com` cannot do anything to a report owned by `user2@email.com`.

Each report also carries per-report permissions:

| Action | Allowed when |
| --- | --- |
| Update | Report is at or before Bounty Calculation, and the hunter has self-initiated updates left or an amend was requested |
| Appeal / Agree | A bounty calculation was sent and no answer has been received yet |
| Data / NDA | Prerequisites were requested |

Permissions are reset automatically on every status change, so an old request cannot be used at a later stage.

## Output Escaping

Every hunter-controlled value (title, notes, severity strings, statuses) is HTML-escaped in outgoing emails. Reviewer notes allow only `<br>`, `<b>`, `<i>` and `<strong>`. Telegram notifications are URL-encoded.

## Email Blacklisting

As described in [Blacklist Rule](settings.md#blacklist-rule), Gerobug blocks and automatically releases addresses with spam-like activity.

## Dashboard Security

* Admin-only pages and actions (Settings, user and notification management, troubleshooting) are enforced server-side.
* Reviewer accounts are addressed by a random public ID, not a sequential database ID.
* Mailbox passwords and webhook URLs are encrypted at rest.
* With the VPN option, the dashboard only accepts connections from private IP ranges.
