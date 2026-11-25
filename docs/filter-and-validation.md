# Filter & Validation

Is Gerobug secure? Nothing is 100% secure, but Gerobug filters and validates everything it receives by default.

## Accepted Email Format

Gerobug only processes emails whose subject matches a known command: `SUBMIT_`,
`CHECK_`, `STATUS_OVERVIEW`, `UPDATE_`, `APPEAL_`, `AGREE_`, `DATA_`/`NDA_`,
`COMMENT_`, `WITHDRAW_`, `MY_SCORE`, `HELP`/`COMMANDS`. Anything else gets a
"we could not process your email" reply pointing at `HELP`. If the subject
starts with a known command but cannot be read, the reply names that command
instead of the generic message.

Reply and forward prefixes are stripped, the separator may be `_`, `:`, `-` or a
space, case is ignored, and a folded long subject is unfolded before the command
is read. Subjects are truncated at 500 characters. See the
[Bug Hunter Guide](bug-hunter-guide.md) for the full format and limits.

## Sender Authentication

Gerobug never replies to or processes a message it cannot trust:

* **Spoofed senders.** If the receiving mail server adds an `Authentication-Results` header, a message whose **SPF and DKIM both fail** is dropped. Without that header, Gerobug falls back to comparing `Return-Path` with `From:` (case-insensitive). A quoted Return-Path such as `<"victim@example.com"@attacker.example>` does not pass as the victim's address.

{% hint style="warning" %}
The `Return-Path` fallback is not real authentication: a sender talking raw SMTP controls both headers. Run Gerobug behind a mail provider that stamps `Authentication-Results` (Gmail and Outlook do).
{% endhint %}

* **No-reply senders** are ignored.
* **Mail loops.** Gerobug ignores mail from its own address, from senders marked `Auto-Submitted` (auto-responders), and from other addresses on its own domain (unless the mailbox is on a free provider such as Gmail). Outgoing mail is marked `Auto-Submitted: auto-generated` and carries a proper `Message-ID`, so two Gerobug instances cannot ping-pong replies.
* **Answered once.** Every inbound message is recorded by `Message-ID`, so marking the mailbox unread does not produce a second reply. Those records are swept after 180 days.

## Report Time

A report's timestamp is the mail server's receive time (the IMAP `INTERNALDATE`),
not the sender-written `Date:` header, so a backdated email cannot make itself
the "original" and flag older reports as duplicates. A message whose server time
cannot be read is skipped rather than trusted.

## Bounce Handling

Delivery status notifications (RFC 3464 DSN) arrive with an empty `Return-Path`.
They are parsed ahead of the spoofing check, logged, and pushed to
Slack/Telegram with the failed recipient, the originating Report ID and the full
SMTP diagnostic, instead of being processed as reports.

A forged bounce cannot be used against a hunter: bounce notifications do not
count toward the sender's rate limit, and bounce alerts are limited to one per
report per hour.

## Hunter Display Names

The name on a certificate and on the Hall of Fame comes from the `From:` display
name, decoded properly (so `=?utf-8?Q?Jos=C3=A9?=` is not stored as mojibake)
and then screened. A name is replaced with `hunter-<6 hex>` when it is shorter
than three characters after normalisation, matches a reserved word such as
`admin` or `security`, or contains (or imitates with look-alike characters) the
platform or company name. A name already used by another hunter gets a suffix.

## Message and File Limits

| Limit | Value |
| --- | --- |
| Raw inbound message | 40 MiB |
| Cumulative MIME payload estimate | 25 MiB |
| MIME parts per message | 32 |
| One PDF attachment | 25 MB |

The IMAP size is checked before the full message is retrieved, but only when the
server supplies valid size metadata; a message without it is skipped. The part
and payload limits also apply while parsing a raw message, and a malformed
transfer encoding cannot bypass the attachment-size preflight.

* Attachments must be valid PDFs. The file is checked in memory and is never written to disk if it is invalid.
* Inline signature images, archives and text files are skipped while looking for the attachment, so the real PDF behind them is still found.
* A PDF over the limit is refused with its own size stated, not dropped silently.
* Files are saved under a server-generated name (`<Report ID>.pdf`, `<Report ID>U1.pdf`, ...). Path traversal is blocked, and an existing file is never overwritten.
* Nothing is counted or stored until the submission has passed validation, so a rejected appeal does not burn an appeal or strand a file.
* Dashboard uploads (templates, logo, signature) are checked by magic bytes, extension and size.

What about malicious PDFs? Since submissions arrive through the mail provider, malicious attachments are usually filtered there first (risk transfer). Open hunter PDFs with care.

## Duplicate Normalisation

Duplicate detection compares the endpoint and the attack type after
normalisation, so spelling differences no longer hide a duplicate:

* Endpoint: scheme (`http://`, `https://`), host case, a leading `www.`, a
  trailing slash, the query string and the fragment are all removed.
* Attack type: compared without case or extra spacing.

The advisory badge goes on the **later** report and links to the original. A new
report can only flag reports that are still in **Need to Review** or **In
Review**. The badge is advisory: always verify manually.

## User Authorization

A hunter can only check or act on reports sent from their own email address. `user1@email.com` cannot do anything to a report owned by `user2@email.com`. Addresses are compared without regard to case.

Each report also carries per-report permissions:

| Action | Allowed when |
| --- | --- |
| Update | Report is at or before Bounty Calculation, and the hunter has self-initiated updates left or an amend was requested |
| Appeal / Agree | A bounty calculation was sent and no answer has been received yet, and fewer than 3 appeals were used |
| Data / NDA | Prerequisites were requested |
| Comment (question) | The report is open (status 1 to 6) and fewer than 10 questions were asked |
| Withdraw | The report is still at Need to Review or In Review |

Permissions are reset automatically on every status change, so an old request cannot be used at a later stage. The status card and the `CHECK_` reply are built from an allowlist of fields, so triage internals cannot leak into them.

## Output Escaping

Every hunter-controlled value (title, notes, severity strings, statuses) is HTML-escaped in outgoing emails. Reviewer notes allow only `<br>`, `<b>`, `<i>` and `<strong>`. Telegram notifications are URL-encoded.

## Email Blacklisting

As described in [Blacklist Rule](settings.md#blacklist-rule), Gerobug blocks and automatically releases addresses with spam-like activity.

## Dashboard Security

* Admin-only pages and actions (Settings, user and notification management, troubleshooting, Hall of Fame management) are enforced server-side.
* Reviewer accounts are addressed by a random public ID, not a sequential database ID.
* Mailbox passwords and webhook URLs are encrypted at rest.
* **Host allowlist.** The dashboard accepts only `127.0.0.1`, `localhost`, the names in `gerobug_dashboard/gerobug_host` and any extra names listed in `GEROBUG_ALLOWED_HOSTS`. A forged `Host` header gets HTTP 400, so it can no longer end up in a password reset link.
* **Secure cookies, optional.** With `GEROBUG_SECURE_COOKIES=true` both the session and the CSRF cookie require HTTPS.
* With the VPN option, the dashboard only accepts connections from private IP ranges.

Both options are read from the dashboard's env file,
`gerobug_dashboard/secrets/gerobug_secret.env` (see
[Installation](installation-and-deployment/#dashboard-host-and-cookie-options)),
not from a root `.env`.
