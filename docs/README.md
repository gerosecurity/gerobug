---
description: v3.1 (Updated 28-10-2026)
---

# What is GEROBUG?

The First Open Source Self-managed Bug Bounty Platform.

Are you a company, planning to have your own bug bounty program, with minimum budget?

**We got you!**

We are aware that some organizations have had difficulty establishing their own bug bounty program. Using a third-party managed platform usually comes with a hefty price tag and increased security concerns. Building your own platform, on the other hand, takes time and effort to build and maintain.

This is where **Gerobug** takes part. Gerobug is an independent, self-hosted platform: a company only needs **one command** to install it and launch a private bug bounty program.

## TL;DR

Gerobug is FREE and helps companies start and manage their own bug bounty program within minutes.

## Main Features

* **Network segregation.** Public pages, dashboard, database and reverse proxy run in separate containers. The public only reaches the static Rules and Guidelines pages.
* **Email-based submission.** Bug hunters submit and follow up on reports by email. Gerobug parses, filters and shows them on the dashboard. Hunters never get an account, so there are no hunter credentials to leak.
* **Encrypted credentials.** Mailbox passwords and notification webhook URLs are encrypted at rest in the database.
* **Automated HTTPS** with NGINX and Let's Encrypt, including optional monthly auto-renewal.
* **Auto reply and notifications** for bug hunters on every action and status change.
* **Slack and Telegram notifications** for new reports, updates, appeals, agreements, submitted data and email delivery failures.
* **Role-based user management** (Admin and Reviewer).
* **Kanban dashboard** with drag-and-drop, search, severity filter and aging indicators.
* **Bounty prerequisites and NDA.** Request the documents you need before paying a bounty, with or without an NDA.
* **Duplicate detection** that flags the later report and links it to the original.
* **CVSS 3.1, CVSS 4.0 and OWASP Risk Rating** calculators.
* **Email blacklisting** (rate limiting) for spammy senders.
* **Automatic certificates of appreciation.**
* **Personalization** with seven built-in themes, custom colors, company name and logo.
* **Troubleshooting tools** for admins: resend email, override report fields, hunter email sinkhole, file recovery and an in-dashboard log viewer.
* **Logging with daily rotation.**
* **Hall of Fame** leaderboard.

## Source Code

[https://github.com/gerosecurity/gerobug](https://github.com/gerosecurity/gerobug) (AGPLv3)
