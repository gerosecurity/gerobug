# Report Detail

The report detail page shows the report data, the hunter's PDF, and **every
hunter submission**, each with its own detail page and PDF download:

* **Updates**
* **Appeals**
* **Hunter Data** (prerequisites and signed NDAs)
* **Hunter Questions** (sent with `COMMENT_<Report ID>`, text only)

Actions per status are described in [Move and Manage Reports](move-and-manage-reports.md).

## Duplicate Of

If the report was flagged as a possible duplicate, or marked invalid naming an
original, the page shows **Duplicate Of** with a link to that report.

## Auto-Accept Countdown

While a report waits at **Bounty Calculation** with no answer from the hunter,
the page shows **Auto-accepts in ...** with the exact date and time. After 30
days with no appeal the report moves to Bounty in Process by itself and the
hunter is told why. The same countdown appears on the Kanban card.

## Decision Reminder

Next to **Send Calculations**, a **Send Reminder** button emails the hunter a
reminder that the decision is still open, stating how much time is left to agree
or appeal.

* Available only while the report is actually waiting for the hunter's decision.
* Refused once the deadline has passed: the report is accepted on the next mail
  check instead.
* **One reminder per 24 hours.** The page shows when the last reminder was sent,
  and an earlier retry says when the next one is possible.
* Needs an active mailbox. Sending a reminder does not change the status, the
  countdown or any permission.

## Update Report Severity

Edit the report and enter a severity vector. Gerobug detects the type and calculates the score:

* **CVSS 3.1**, for example `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
* **CVSS 4.0**, for example `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N`
* **OWASP Risk Rating**, for example `(SL:1/M:1/O:0/S:2/ED:1/EE:1/A:1/ID:1/LC:2/LI:1/LAV:1/LAC:1/FD:1/RD:1/NC:2/PV:3)`

Built-in CVSS and OWASP calculators help you build the vector. The reviewer who set the severity is recorded.

| Score | Label | Hall of Fame weight |
| --- | --- | --- |
| 0.0 | Informational | none |
| 0.1 - 3.9 | Low | 1 |
| 4.0 - 6.9 | Medium | 2 |
| 7.0 - 8.9 | High | 3 |
| 9.0 - 10.0 | Critical | 4 |

The severity decides the points a completed report awards: `int(score)` times
the weight. See [Hall of Fame](../hall-of-fame.md).
