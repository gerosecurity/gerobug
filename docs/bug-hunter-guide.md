# Bug Hunter Guide (Email Commands)

Bug hunters interact with Gerobug only by email. The program's address and these templates are shown on the public page `https://[your-domain]/submit/`.

Each command is identified by the **email subject**. Anything else is answered with an "Invalid Report Format" reply.

## Submit a Report

```
Subject: SUBMIT_<Report Title>
Body:
TYPE= Bug type (example: XSS, SQL Injection, IDOR)
ENDPOINT= Affected endpoint
SUMMARY= Summary of the finding

Attachment: PDF report file (use the report template)
```

* Title: 3 to 100 characters
* Type and endpoint: required, up to 100 characters each
* Summary: at least 10 characters
* Exactly one valid PDF, under 25 MB

The hunter receives a confirmation with the **Report ID** (12 characters), which is needed for every other command.

{% hint style="info" %}
Do not attach PoC videos, archives (.zip/.rar) or exploit code: mail filters strip them. Upload them to Google Drive, OneDrive, Dropbox, a private GitHub repository or a secret Gist, and put the link (and password, if any) inside the PDF.
{% endhint %}

## Check Report Status

```
Subject: CHECK_<Report ID>
```

## Check All Report Status (Overview)

```
Subject: STATUS_OVERVIEW
```

Returns a table of all the hunter's reports and their status.

## Update a Report

```
Subject: UPDATE_<Report ID>
Body: Summary of the update
Attachment: PDF report file (optional if the body explains the update)
```

* 3 self-initiated updates per report. Updates requested by the program are free.
* Accepted until the report leaves Bounty Calculation.

## Appeal a Bounty Calculation

```
Subject: APPEAL_<Report ID>
Body: Reason for the appeal
```

Only after a bounty calculation has been sent. Up to 3 appeals per report.

## Agree to a Bounty Calculation

```
Subject: AGREE_<Report ID>
```

Without an appeal, the calculation is accepted automatically after 30 days.

## Submit Data and NDA

```
Subject: DATA_<Report ID>
Body: Requested information
Attachment: Signed NDA PDF (required only if an NDA was requested)
```

Only after the program has requested prerequisites. The older `NDA_<Report ID>` subject is still accepted.

## Check Score

```
Subject: MY_SCORE
```

Returns the hunter's total points, which are also shown on the Hall of Fame.

## Common Replies

| Reply | Meaning |
| --- | --- |
| Invalid Report Format | Unknown subject, missing/invalid PDF, or fields too short/long |
| Invalid Report ID | The Report ID does not exist |
| Authorization Failure | The report belongs to another email address, or the action has not been requested |
| Update Limit Reached | The 3 self-initiated updates are used; wait for an amend request |
| Updates Closed | The report has moved past Bounty Calculation |
| Appeal Limit Reached | 3 appeals used; the determination is final |
| Temporary Restriction | Too many emails in a short time; the address is blocked temporarily |
| Bounty Accepted by Default | No appeal within 30 days; the calculation was accepted |
