# Troubleshooting

**Settings > Troubleshooting** is available to the admin only.

## Hunter Email Sinkhole

Silently drops **every outgoing email to hunters** while enabled. Use it during maintenance or data corrections so hunters do not receive confusing notifications. A banner is shown on every dashboard page until it is turned off. Who enabled it and when is recorded.

## Resend Email

Replays the last email a reviewer sent for a report, for example after a bounce:

* Invalid notice
* Amend request
* Bounty calculation
* Prerequisites/NDA request
* Status change notification
* Completion certificate (the certificate is rebuilt)

No status, score or permission changes. Resending a bounty calculation while the report is still at Bounty Calculation **restarts the 30-day appeal window**, since that is when the hunter can actually read it.

Only emails sent after upgrading to this version can be resent.

## Override Report Fields

Load a report by ID and correct its title, status, endpoint, attack type, duplicate flag or hunter name without touching the database. Every override is logged with old and new values.

{% hint style="warning" %}
Changing the status here does not email the hunter. It does reset the hunter's permissions for the new status.
{% endhint %}

## Recover Lost Report Files

Searches the mailbox for the original emails of reports, updates and NDAs whose PDF is missing on disk, and restores the attachments. Requires an active mailbox. Progress is written to the log.

## Server Logs

Shows the last lines of `gerobug.log` (10 to 2000 lines) in the dashboard, so you can check delivery and parser activity without shell access.
