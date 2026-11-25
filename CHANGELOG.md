# Changelog

## Unreleased

### Changed

- **Hall of Fame points are weighted by severity.** Each completed report adds
  its severity score, rounded down, times 1 for Low, 2 for Medium, 3 for High
  and 4 for Critical. On upgrade every hunter's score is recomputed once from
  their completed reports, which replaces any manual score correction made in
  Settings > Hall of Fame.

### Hall of Fame

- **Scores stay in sync with Completed.** Completing a report awards the hunter
  its severity points, and moving a report back out of Completed takes exactly
  those points away again. Every path is covered: the completion email (code
  704), Troubleshooting > Override Report Fields, the Kanban board and any
  future path, because the award now happens in one place when the status
  changes. A score can never go below zero.
- **New operator tool: Settings > Troubleshooting > Hall of Fame**
  (superuser only). Search hunters by email or name, then per hunter: set the
  score by hand, hide the hunter from the public Hall of Fame without losing
  their score, recompute the score from their completed reports, or delete a
  hunter who has no reports at all. A hunter with reports can only be hidden,
  so their certificates can still be resent. Recompute All recomputes every
  hunter and needs a typed RECOMPUTE confirmation. Every action is written to
  the server log.
- **Hidden hunters** no longer appear on the public Hall of Fame page, and
  still receive MY_SCORE replies with their real score.

### Reports

- **Send Reminder for a bounty decision** (code 706). A report waiting for the
  hunter to agree or appeal can be reminded from the report page, next to Send
  Calculations. The reminder repeats the severity, the time left to agree or
  appeal, and what happens if the hunter does not answer. It is refused when
  the report is not waiting for a decision, when the deadline has already
  passed, and for 24 hours after the last reminder. Every reminder is written
  to the server log.
- **An override that changes the status clears the stale last email.**
  Troubleshooting > Override Report Fields no longer leaves the previous email
  code and note on a report whose status it just moved.

### Fixed

- **Long subjects are no longer rejected or stored broken.** Mail clients fold
  a subject longer than about 69 characters onto two lines. The folded line
  break is now removed before the command is read, so the title is stored
  without stray line breaks. A subject that starts with a known command but
  can't be read now gets a reply naming that command, not the generic
  "could not recognise the command" message.

### Security

- **Password reset links can no longer be pointed at another host**
  (4E0A67B01C7D). `ALLOWED_HOSTS` was `*`, so a forged `Host` header ended up
  in the reset link. The dashboard now accepts only `127.0.0.1`, `localhost`
  and the names in `gerobug_host`.
- **Forged bounces can no longer blacklist a hunter** (5365C079BAD4).
  Bounce notifications no longer count toward the sender's rate limit, and
  bounce alerts are limited to one per report per hour. A quoted Return-Path
  (`<"victim@example.com"@attacker.example>`) no longer passes as the victim's
  address. Blacklist and watchlist keys ignore case. The no-reply check no
  longer slows down on long addresses.
- **Report time comes from the mail server, not the sender's `Date:`
  header** (D5D16D93C90A). A backdated report could make itself the
  "original" and flag older reports as duplicates. A new report can now only
  flag reports still in Need to Review or In Review.
- **Hunter display names are screened** (B5F277882DB3). Names that match a
  reserved word (`admin`, `security`, ...), contain the platform or company
  name, or imitate one with look-alike characters are replaced with
  `hunter-<6 hex>`. A name already used by another hunter gets a suffix.
- **Recovery uses certificate-verified IMAP TLS and the configured port**, and
  checks the fetched sender and the exact decoded subject before storing
  attachments. Recovery considers only a matching sender and normalized full
  subjects, including reply prefixes and legacy NDA subjects.
- **Operator actions lock and recheck report state.** Completion moves 6 to 7
  once, and the score change commits before certificate generation and mail
  delivery. A failed delivery needs an explicit administrator resend, not
  another completion.
- **Intake is bounded before any decoding.** Raw messages are limited to
  40 MiB, the cumulative MIME payload estimate to 25 MiB and MIME parts to 32,
  all before attachment decoding. The existing 25 MB per-PDF limit remains.
  IMAP size metadata is checked before full retrieval, and a message whose
  server supplies no valid size metadata is skipped. The MIME part limit also
  applies while parsing a raw message, and a malformed transfer encoding
  cannot bypass the attachment-size preflight.
- **Report actions enforce their status rules on the server.** Mark as Invalid
  is accepted only in Need to Review and In Review, Move only from Need to
  Review through Fixing (Retest), and Delete only for Not Valid reports,
  matching the buttons on the report page. Reopening a Not Valid report stays
  available to superusers through Settings > Troubleshooting > Override Report
  Fields.

### Upgrade notes

- **HTTP installs reached by a name not in `gerobug_host`** (for example a
  public IP behind NAT) now get HTTP 400. Add the extra names, separated by
  commas, as `GEROBUG_ALLOWED_HOSTS=...` in
  `gerobug_dashboard/secrets/gerobug_secret.env` and restart.
- **HTTPS dashboard deployments** can set `GEROBUG_SECURE_COOKIES=true` in
  `gerobug_dashboard/secrets/gerobug_secret.env`. Both the session and the CSRF
  cookie then require HTTPS. The default stays false for existing local HTTP
  tunnels.
- Report titles stored with line breaks from folded subjects are unfolded once
  on first boot.
- Two new fields are added: `report_score_awarded` on a report (the points that
  report currently contributes) and `hunter_hidden` on a bug hunter.
- On upgrade every hunter's Hall of Fame score is recomputed once from their
  completed reports, which replaces any manual score correction. Completed
  reports are back-filled with the points they awarded, so a later move out of
  Completed subtracts the right amount. The backfill is idempotent.
- Existing stored attachments and scores are not retrospectively repaired.
  Existing Settings > Rules text is preserved; administrators should
  communicate the new message limits to hunters.

## v4.0 - 29 OCT 2026

Every hunter email action is now correct, forgiving about formatting and able
to explain itself. CHECK answers with a card that says what the hunter should
do next, three new commands fill the gaps hunters kept writing to us about,
and the Submit page documents all of it.

### Hunter actions

- **HELP** (or **COMMANDS**) replies with every command, a one line
  description of each, and the remaining allowances of each report the sender
  still has open. A sender with no reports gets the command list only.
- **COMMENT_<Report ID>** lets a hunter ask the team a question without
  spending one of their three updates. Text only, 10 per report, allowed while
  the report is open. Questions show on the report page in the dashboard. On a
  closed or completed report the reply says questions are closed and names the
  stage, rather than reporting an authorization failure.
- **WITHDRAW_<Report ID>** closes a report the hunter no longer wants pursued,
  while it is still waiting for a triager or in review. It drops every open
  grant and is recorded as a withdrawal, not as an invalid report, so
  Troubleshooting > Resend never replays an "Invalid Report" notice for it.
  Later than that the reply names the current stage and offers a plain reply
  instead. An operator can reverse a withdrawal from
  Troubleshooting > Override Report Fields.
- **Subjects are forgiving.** `Re:`, `Fwd:`, `[EXT]` and similar prefixes,
  lower case, spaces inside a Report ID, and a trailing word or suffix after
  the Report ID are all accepted, so `CHECK_AB12CD34EF56 thanks` works. Every
  operator email that asks for something now carries a subject the hunter can
  simply reply to.
- **Replies are threaded**, so a hunter's mail client groups all the messages
  about one report into one conversation.
- **An email is answered once.** Inbound mail is deduplicated by Message-ID,
  so marking the mailbox unread no longer makes Gerobug reply all over again.
- **Clear refusals.** A PDF over 25 MB states its own size (the 25 MB limit
  itself is accepted), a non-PDF attachment says so, and a short SUBMIT names
  the field that is too short. Inline signature images, archives and text files
  are skipped, so the real PDF behind them is still found. Nothing is counted
  or stored until the submission has passed validation, so a rejected appeal no
  longer burns an appeal or strands a file.
- **AGREE is atomic** and sends one confirmation naming the new stage.

### Status card

- **CHECK replies with a report card**: the stage and since when, what we need
  from the hunter next with a button for it, the remaining update and appeal
  allowance, every submission the hunter has sent, the last message we sent,
  and the original submission. It is built from an allowlist, so triage
  internals cannot leak into it.
- **STATUS_OVERVIEW is an index** of every report, with a "Needs you" column,
  the reports that need the hunter listed first, and a link per Report ID that
  asks for its card.
- **One-click buttons** in the emails that ask for something: update, agree,
  appeal, send data.

### Submit page

- Grouped sections for all eleven commands, each with its subject, its body
  format and the rules that apply, stating the real limits.
- A Report ID box that fills the ID into every subject and mail button on the
  page. Nothing is sent or stored; the ID stays in the browser.
- An "Open in mail app" button per section, with the SUBMIT one pre-filling
  the body template.
- A "What happens next" list explaining all seven stages, in the same words
  the emails use.

### Fixed

- Inbound mail is parsed as bytes, so Latin-1 and other 8-bit emails no longer
  vanish, and a missing or broken Date header no longer drops the message.
- SUBMIT and APPEAL use the shared body extractor, so an email whose only
  content is an attachment no longer crashes the parser.
- SUBMIT bodies are parsed line by line, so lower case labels, colons, dashes
  and markdown bold all work, and a summary mentioning the word ENDPOINT stays
  intact.
- Report IDs are random and unique, instead of being derived from the hunter's
  address and the clock.
- File recovery covers every submission, appeals included, and picks the
  message closest to the row's own date.
- Deleting a report now really deletes its updates, appeals, data submissions
  and questions. The old cleanup never ran on Django 4.
- MY_SCORE and STATUS_OVERVIEW from a sender with no reports answer with a
  "no reports yet" reply instead of an authorization failure.

### Hunter lifecycle

- **Unappealed bounties are accepted automatically.** A bounty calculation
  with no appeal for 30 days is treated as agreed: the report moves from
  Bounty Calculation to Bounty in Process and the hunter is told why. The
  countdown shows on the report detail page and on the Kanban card.
- **Hunters may send 3 updates on their own initiative.** An update requested
  by the triager is free and does not count. Once the allowance is spent the
  hunter gets a clear "update limit reached" reply instead of "not authorized".
- **Updates close after Bounty Calculation.** A late update gets an "updates
  closed" reply naming the current stage.
- **Appeal allowance is stated.** Every appeal confirmation says how many are
  left, and a fourth appeal gets "determination is final" instead of
  "not authorized".
- **Every hunter submission is listed.** The report detail page lists all
  updates, appeals and data submissions, newest first, each with its own
  detail link and PDF download.
- **Hunter emails restyled** to a single inline-styled layout.

### Troubleshooting

Settings > Troubleshooting gains four tools (superuser only):

- **Resend Email.** Replays the last email a triager sent for a report
  (invalid notice, amend request, bounty calculation, NDA/prerequisite
  request, status notification, completion certificate) after a bounce. No
  status, score or permission changes. Resending a bounty calculation while
  the report is still at Bounty Calculation restarts the hunter's 30-day
  appeal window, since that is when they can actually read it.
- **Override Report Fields.** Correct a report's title, status, endpoint,
  attack type, duplicate tag or hunter name without touching the database.
- **Hunter Email Sinkhole.** Silently drops every outgoing hunter email while
  on, with a banner on every page until it is turned off.
- **Server Logs.** Tail gerobug.log from the dashboard.

### Mail security and duplicates

- **Spoofed senders are rejected using the mail server's verdict.** When the
  receiving mail server stamps an `Authentication-Results` header, a message
  whose SPF and DKIM both fail is dropped, even if its `Return-Path` matches
  `From:`. Without that header the old `Return-Path` comparison still applies,
  now case-insensitive. That fallback is not real authentication: a sender
  talking raw SMTP controls both headers. Run Gerobug behind a mail server
  that stamps `Authentication-Results`.
- **Hunter names are decoded properly.** Names like
  `=?utf-8?Q?Jos=C3=A9_Sachs?=` reached the certificate as
  `utf-8QJosC3A9_Sachs`, and a bare `From: me@example.com` lost its last
  character.
- **Duplicate detection ignores spelling differences.** Scheme, host case,
  `www.`, trailing slash, query string and fragment no longer make the same
  endpoint look different, and attack types compare without case or spacing.
  The badge goes on the later report and links to the original.
- **Mark as Invalid can name the original** of a duplicate. The report detail
  page shows it as a link.

### Upgrade notes

- New tables: `ProcessedMail` (inbound dedupe, swept after 180 days) and
  `BugReportHunterComment`.
- New fields on `BugReport`: `report_status_changed_at` and
  `report_hunter_comment`.
- Reports that existed before the upgrade show no "since" date on their card
  until their stage next changes.
- A Settings > Rules text saved before the upgrade keeps whatever command list
  it contained until you edit it.
- New report IDs are random hex. Existing report IDs keep working.
- MY_SCORE and STATUS_OVERVIEW from a sender with no reports changed from 403
  to a new "no reports yet" reply.
- A bounty decision still needs an explicit AGREE or APPEAL. A plain reply to
  the decision email is not treated as agreement.
- The submission guidelines gained a bullet asking hunters to share videos,
  archives and exploit code as links inside the PDF. Installations that already
  have their rules saved keep the stored text, so paste the bullet into
  Settings > Rules if you want it.
- Reports already at Bounty Calculation before the upgrade never auto-accept,
  because their hunters were not told about the 30-day window. Re-send the
  calculation (report page or Troubleshooting > Resend) to start it. Resend
  only knows about emails sent after the upgrade.

## v3.1 — 25 OCT 2026

### Interface

- **New design system.** The dashboard and the public pages share one skin,
  driven by the colors already configured in Settings > Personalization. Every
  surface, accent and action color derives from them, so the interface follows
  your palette rather than overriding it.
- **Seven selectable themes.** Settings > Personalization gains a preset
  gallery (Gero Dark, Gero Classic, Route, Midnight, Forest, Royal, Graphite)
  with a live preview. Picking one fills the color pickers; nothing is saved
  until you click Update, and a reset button restores the defaults.
  Every preset is contrast-checked against WCAG AA for the text the interface
  actually draws on it.
- **Kanban drag-and-drop.** Reports can be dragged between columns on the
  board instead of being opened one at a time. The board also gains a
  search/severity filter bar and an aging indicator, and sorts the
  highest-severity report to the top of each column. Hunters receive the same
  status-change notification as the existing forward button.
- **Severity names** are shown on the board and the status tables, rather than
  only the numeric score.

### Upgrade note

The palette shipped before this release used near-white colors for two roles
the design system fills with light text, which would have been unreadable. On
first boot, an installation still using those original colors is moved onto
the new defaults automatically. **If you have customized any of your six
theme colors, nothing is changed** — your palette is left exactly as it is,
and the original look is available as the "Gero Classic" preset. No action is
required either way.

### Security

- **Outbound emails escape every hunter-controlled value.** Report titles,
  reviewer notes, severity strings, status values and the status-overview table
  rows were interpolated into the HTML mail body unescaped, so a crafted report
  title could inject markup into the message a hunter received. All wildcards
  are now escaped, and the reviewer note passes through a formatter that
  escapes everything and allows back only `<br>`, `<b>`, `<i>` and `<strong>`.
- **Telegram notifications URL-encode their payload.** A report title
  containing `&` or `#` previously truncated the notification. A Markdown
  parse failure now retries as plain text instead of being dropped.

### Email delivery visibility

- **Bounces are detected and reported.** Delivery-status notifications
  (RFC 3464 DSN) arrive with an empty `Return-Path` and were being discarded by
  the spoofing check before anything looked at them. They are now parsed ahead
  of that check, logged, and pushed to Slack/Telegram with the failed
  recipient, the originating Report ID and the full SMTP diagnostic — which was
  previously cut off at the first folded line.

### Fixes

- Appreciation certificates render `INFO` for informational findings, which
  were mislabelled `LOW`.
- Deleting a report that has no attachment folder no longer raises a 500.
- Report fields widened so long titles stop being truncated on save: title and
  endpoint to 255 characters, attack type to 255, reviewer to 50.

### Project

- **Continuous integration.** `ruff` correctness linting, Django system checks
  and the test suite now run against PostgreSQL 17 on every push to `main`,
  `development` and `feature/**`, and on every pull request.
- **Documented release process.** Branch rules, the staging smoke-test
  checklist, deploy, hotfix and rollback procedures live in
  [DEVELOPMENT.md](DEVELOPMENT.md).
- Shell scripts are pinned to LF endings, so a Windows checkout can no longer
  bake a broken container entrypoint into the images.

### Internal

- `geronotify` lost five duplicated per-action blocks per channel in favour of
  a single message table.
- The three upload validators share one magic-byte/extension/size check.
- Removed `gerosecure.clean()` (no callers) and six unused imports.
