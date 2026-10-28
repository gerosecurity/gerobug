# Changelog

## Unreleased

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

### Upgrade note

The submission guidelines gained a bullet asking hunters to share videos,
archives and exploit code as links inside the PDF. Installations that already
have their rules saved keep the stored text, so paste the bullet into
Settings > Rules if you want it. Reports already at Bounty Calculation before
the upgrade never auto-accept, because their hunters were not told about the
30-day window; re-send the calculation (report page or Troubleshooting >
Resend) to start it. Resend only knows about emails sent after the upgrade.

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
