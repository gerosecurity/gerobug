# Move and Manage Reports

Available actions depend on the status. Every status change, whether by button or by drag and drop on the dashboard, emails the hunter.

| Status | Actions |
| --- | --- |
| Need to Review | Move forward, Mark as Invalid |
| In Review | Request Amend, Move forward, Mark as Invalid |
| Fixing, Fixing (Retest) | Request Amend, Move forward |
| Bounty Calculation | Send Calculations, Send Reminder |
| Bounty in Process | Request Prerequisites (with or without NDA), Complete |
| Not Valid | Delete |

All reasons and notes must be at least 10 characters and are included in the email to the hunter.

## Mark as Invalid

Moves the report to Not Valid and emails the reason to the hunter. Optionally enter the **original Report ID** to mark it as a duplicate; the detail page then links to the original.

## Request Amend

Asks the hunter for more information. It grants one extra update that does not count toward the hunter's own allowance of 3.

## Bounty Calculation and Appeals

When the report reaches Bounty Calculation, send the calculation to the hunter. The hunter can then:

* **Agree** (`AGREE_<Report ID>`): the report moves to Bounty in Process, and one confirmation naming the new stage is sent.
* **Appeal** (`APPEAL_<Report ID>`): you review the appeal and send a new calculation. Each report allows **3 appeals**. Every appeal confirmation states how many remain; after the third, the determination is final.
* **Do nothing:** if there is no appeal within **30 days** of the calculation being sent, it is **accepted automatically**. The report moves to Bounty in Process and the hunter is told why. Slack and Telegram get the same agreement notification as for an explicit AGREE.

The countdown is visible on the report detail page and on the Kanban card. Use
**Send Reminder**, next to Send Calculations, to nudge the hunter before the
deadline: at most one reminder per 24 hours, and never after the deadline has
passed. See [Report Detail](report-detail.md#decision-reminder).

{% hint style="info" %}
Resending a bounty calculation from **Troubleshooting > Resend Email** does not
restart the 30 days. The countdown always runs from the original decision email.
{% endhint %}

## Prerequisites and NDA

At Bounty in Process, request what you need to pay the bounty (for example bank or identity details). Tick **Require NDA** to also send the NDA template for signing, or untick it to request data only. The hunter replies with `DATA_<Report ID>`; the signed NDA PDF is optional when no NDA was requested.

## Complete

Marks the report as Completed, awards the hunter the report's Hall of Fame
points (the severity score, rounded down, times the band weight), generates the
certificate of appreciation and emails it to the hunter with your note.

Moving a completed report back out of Completed, from the board or from
Troubleshooting > Override Report Fields, takes exactly those points away again.

## Kanban Board

Drag a card between columns to change its status. The hunter receives the same
status-change email as when using the forward button, and the Hall of Fame
points follow the move in both directions.

## Withdrawn Reports

A hunter can withdraw a report with `WITHDRAW_<Report ID>` while it is still at
Need to Review or In Review. It closes as a withdrawal, not as an invalid
report, so Resend Email never replays an "Invalid Report" notice for it. To
reverse a withdrawal, move the report back with
[Override Report Fields](../troubleshooting.md#override-report-fields).

## Delete

Deletes the report and its files, together with its updates, appeals, data
submissions and questions.

{% hint style="info" %}
Email templates cannot be edited from the dashboard. To change them, edit `gerobug_dashboard/geromail/mail_templates.py`.
{% endhint %}
