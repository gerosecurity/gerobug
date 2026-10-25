# Changelog

## v3.1 — 25 OCT 2026

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
