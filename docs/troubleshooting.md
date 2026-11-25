# Troubleshooting

**Settings > Troubleshooting** is available to the admin (superuser) only.
Reviewers cannot reach these tools, and the restriction is enforced
server-side. Every action is written to `gerobug.log` with the username that
performed it.

## Recover Lost Report Files

Searches the mailbox for the original emails of reports, updates, appeals and
data submissions whose PDF is missing on disk, and restores the attachments.
Requires an active mailbox. Progress is written to the log.

Recovery only accepts a candidate message when both the sender and the full
decoded subject match the row it is restoring, including reply prefixes and the
legacy `NDA_` subjects, and it picks the message closest to the row's own date.

## Resend Email

Replays the last email an operator initiated for a report, for example after a
bounce:

| Resendable | |
| --- | --- |
| Invalid Report Notification | Status Update Notification |
| Amend / Update Request | Bounty Calculation |
| NDA & Prerequisites Request | Prerequisites Request (no NDA) |
| Completion (Certificate), rebuilt before sending | |

Automated replies to the hunter (invalid format, authorization failure, unknown
Report ID) are never resent, and a withdrawal is recorded as a withdrawal, so
Resend never replays an "Invalid Report" notice for it.

The original message text, reasons and attachments are sent as-is. No status,
score or permission changes are made.

{% hint style="info" %}
Resending a bounty calculation does **not** restart the auto-accept countdown.
The 30 days still run from the original decision email. To nudge the hunter
before the deadline, use **Send Reminder** on the report page instead (see
[Report Detail](usage/report-detail.md#decision-reminder)).
{% endhint %}

Only emails sent after upgrading to this version can be resent. If no
operator-initiated email is recorded for a report, send the email from the
report page instead.

## Override Report Fields

Load a report by ID and correct its title, status, endpoint, attack type,
duplicate flag or hunter name without touching the database. Every override is
logged with old and new values.

* Changing the status here does **not** email the hunter. It does reset the
  hunter's permissions for the new status.
* Changing the status into or out of **Completed** awards or revokes the
  report's Hall of Fame points, exactly like the completion email does.
* Changing the hunter name affects all of that hunter's reports and the Hall of
  Fame.
* This is also how you reverse a hunter's `WITHDRAW_`: move the report back to
  Need to Review or In Review.

## Hall of Fame

Search hunters, then set a score by hand, hide a hunter from the public page,
recompute one hunter from their completed reports, or delete a hunter with no
reports. **Recompute all** needs a typed `RECOMPUTE` confirmation. Full details
in [Hall of Fame](hall-of-fame.md#operator-tool).

## Hunter Email Sinkhole

Silently drops **every outgoing email to hunters** while enabled. Use it during
maintenance or data corrections so hunters do not receive confusing
notifications. A banner is shown on every dashboard page until it is turned off.
Who enabled it and when is recorded, and each suppressed message is logged.

## Server Logs

Shows the last lines of `gerobug.log` (10 to 2000 lines) in the dashboard, so
you can check delivery and parser activity without shell access. See
[Logging & Debugging](logging-and-debugging.md) for how to read it.
