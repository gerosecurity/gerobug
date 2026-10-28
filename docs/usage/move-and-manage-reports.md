# Move and Manage Reports

Available actions depend on the status. Every status change, whether by button or by drag and drop on the dashboard, emails the hunter.

| Status | Actions |
| --- | --- |
| Need to Review | Move forward, Mark as Invalid |
| In Review, Fixing, Fixing (Retest) | Request Amend, Move forward, Mark as Invalid |
| Bounty Calculation | Send Bounty Calculation |
| Bounty in Process | Request Prerequisites (with or without NDA), Complete |

All reasons and notes must be at least 10 characters and are included in the email to the hunter.

## Mark as Invalid

Moves the report to Not Valid and emails the reason to the hunter. Optionally enter the **original Report ID** to mark it as a duplicate; the detail page then links to the original.

## Request Amend

Asks the hunter for more information. It grants one extra update that does not count toward the hunter's own allowance.

## Bounty Calculation and Appeals

When the report reaches Bounty Calculation, send the calculation to the hunter. The hunter can then:

* **Agree** (`AGREE_<Report ID>`): the report moves to Bounty in Process.
* **Appeal** (`APPEAL_<Report ID>`): you review the appeal and send a new calculation. Each report allows **3 appeals**. Every appeal confirmation states how many remain; after the third, the determination is final.
* **Do nothing:** if there is no appeal within **30 days** of the calculation being sent, it is **accepted automatically**. The report moves to Bounty in Process and the hunter is told why.

## Prerequisites and NDA

At Bounty in Process, request what you need to pay the bounty (for example bank or identity details). Tick **Require NDA** to also send the NDA template for signing, or untick it to request data only. The hunter replies with `DATA_<Report ID>`; the signed NDA PDF is optional when no NDA was requested.

## Complete

Marks the report as Completed, adds the severity score to the hunter's Hall of Fame points, generates the certificate of appreciation and emails it to the hunter with your note.

## Delete

Deletes the report and its files.

{% hint style="info" %}
Email templates cannot be edited from the dashboard. To change them, edit `gerobug_dashboard/geromail/mail_templates.py`.
{% endhint %}
