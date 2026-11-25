# Gerobug: The First Open Source Bug Bounty Platform.

![gerobugLogo](https://raw.githubusercontent.com/gerosecurity/gerobug-docs-images/main/logo.png)

![CI](https://github.com/gerosecurity/gerobug/actions/workflows/ci.yml/badge.svg)
![CodeQL](https://github.com/gerosecurity/gerobug/actions/workflows/github-code-scanning/codeql/badge.svg)
[![License](https://img.shields.io/badge/License-AGPLv3-red.svg?&logo=none)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-4.0-blue)](CHANGELOG.md)
[![Black Hat Arsenal Asia 2023](https://img.shields.io/badge/Black%20Hat%20Arsenal-Asia%202023-black?style=flat&labelColor=555)](https://www.blackhat.com/asia-23/arsenal/schedule/index.html#gerobug-open-source-private-self-managed-bug-bounty-platform-31241)
[![Black Hat Arsenal Asia 2024](https://img.shields.io/badge/Black%20Hat%20Arsenal-Asia%202024-black?style=flat&labelColor=555)](https://www.blackhat.com/asia-24/arsenal/schedule/#gerobug-the-first-open-source-bug-bounty-platform-37538)

# Gerobug
__The first open source self-managed bug bounty platform.__

Are you a company, planning to have your own bug bounty program, with minimum budget?<br>

__WE GOT YOU!__

We are aware that some organizations have had difficulty establishing their own bug bounty program.<br>
Using a third-party managed platform usually comes with a hefty price tag and security risks. _(If you know, you know...)_<br>
In the other hand, creating your own self-managed platform will take time and effort to build and maintain it.

<br>

## What's New in v4
- __Every hunter action works by email:__ SUBMIT, CHECK, STATUS_OVERVIEW, MY_SCORE, HELP, UPDATE, COMMENT, DATA, AGREE, APPEAL and WITHDRAW. Subjects are forgiving (`Re:`, lower case, extra words after the Report ID) and replies are threaded per report.
- __Status card:__ CHECK answers with the report's stage, what we need from the hunter next, the remaining update and appeal allowance and every submission sent so far.
- __Fair, predictable lifecycle:__ 3 self-initiated updates, 3 appeals, and an unappealed bounty is accepted automatically after 30 days.
- __Severity-weighted Hall of Fame:__ each completed report adds its severity score, rounded down, times 1 for Low, 2 for Medium, 3 for High and 4 for Critical.
- __Operator tools:__ Send Reminder for a pending bounty decision, plus Troubleshooting tools to resend an email, override report fields, pause hunter email and manage Hall of Fame entries.
- __New look:__ a shared design system for the dashboard and public pages, seven theme presets and a drag-and-drop Kanban board.
- __Hardened mail intake:__ spoofed senders, forged bounces, backdated reports and oversized messages are rejected before they reach the dashboard.

Full details and upgrade notes are in the [CHANGELOG](CHANGELOG.md).

<br>

## Why Gerobug?
- __EASY        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Have your bug bounty program running with just single line of command
- __SECURE      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Gerobug uses email parser and network segregation to minimize security risks.
- __OPEN SOURCE &nbsp;&nbsp;&nbsp;&nbsp;:__ It is FREE.

<br>

## (Minimum) Recommended Specification
* Ubuntu 24.04
* vCPU 2 Core
* RAM 2 GB
* HDD 16 GB

<br>

## Requirements
* <a href="https://support.google.com/accounts/answer/185833">Gmail</a> or <a href="https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944">Outlook</a> Email with <b>App password</b> implemented
* VPN Server (Recommended for Production Server)
* Domain for HTTPS (Recommended for Production Server)
* Port 80, 443, 6320
* Python 3.x
* Docker 
* Docker Compose v2

__(You don't need to install anything manually, we'll do it for you!)__

<br>

## Deployment and Usage
To deploy gerobug:
1. Clone this repository
```bash
git clone https://github.com/gerosecurity/gerobug
cd gerobug
```
2. Run the Setup Script: 
```bash
./gerobug.sh
```
3. Follow the setup instructions (Read the [documentation](https://gerobug.gitbook.io/documentation/) for details)
4. By default, Gerobug Dashboard will listen at port __6320__

Access the login page at `http://[Domain/IP]:6320/login`<br>
<br>__Credential__<br>
Username&nbsp;&nbsp;: `geromin`<br>
Password&nbsp;&nbsp;&nbsp;: Randomly generated at `gerobug/gerobug_dashboard/secrets/gerobug_secret.env`

<br>

## Upgrading to v4
Run `./gerobug.sh` and choose __2) UPDATE__. Your reports, hunters, settings and files are kept. Before upgrading, read the upgrade notes in the [CHANGELOG](CHANGELOG.md), in particular:
- The dashboard now only answers to `127.0.0.1`, `localhost` and the names in `gerobug_host`. If you reach it by another name (for example a public IP behind NAT), add `GEROBUG_ALLOWED_HOSTS=name1,name2` to `gerobug_dashboard/secrets/gerobug_secret.env` and restart.
- On HTTPS deployments, set `GEROBUG_SECURE_COOKIES=true` in the same file.
- Every hunter's Hall of Fame score is recomputed once from their completed reports, which replaces any manual score correction.
- Settings > Rules text you saved earlier is kept as it is. Update it to tell hunters about the new commands and limits.

<br>

You can read the __detailed documentation [here](https://gerobug.gitbook.io/documentation/)__

<br>

## Main Features
- Network Segregation<br>
All services are running on seperate containers. Public users should only able to access the static page (Rules and guidelines).

- Encrypted Credentials<br>
Mailbox passwords and notification webhook URLs are encrypted at rest in the database.

- Easy and Quick Installation<br>
Use our run script to install Gerobug, its quick and easy!

- HTTPS Implementation<br>
Automated HTTPS configuration using NGINX and Let's Encrypt.

- Homepage<br>
This should be the only page accessible by public, which contains Rules and Guidelines for your bug bounty program.

- Email Parser<br>
Bug Hunter will submit their findings by email, which Gerobug will parse, filter, and show them on dashboard. Sender authentication results, bounce notifications and message sizes are checked before anything is stored.

- Auto Reply and Notification for Bug Hunters<br>
Bug Hunter's inquiries will be automatically replied and notified if there any updates on their report. Hunters run the whole lifecycle by email: submit, check a report's status card, list all their reports, update, ask a question, send requested documents, agree or appeal a bounty decision, withdraw a report, and ask for the command list with HELP. The Submit page documents every command.

- Bug Hunter Lifecycle<br>
Hunters get 3 self-initiated updates and 3 appeals per report, and a bounty decision that is not appealed within 30 days is accepted automatically. Operators can send a reminder while a decision is pending.

- Notification Channel<br>
Company will also be notified via Slack/Telegram if there any new report, and when an email to a hunter bounces.

- User Management<br>
Gerobug has a role-based user management.

- Report Management<br>
Manage reports easily using a kanban model dashboard, with drag-and-drop, search, severity filters and an aging indicator.

- Bounty Prerequisites and NDA<br>
Request the documents you need before paying a bounty, with or without an NDA, and track what the hunter sends back.

- Report Filtering and Flagging<br>
Reports from Bug Hunter will be filtered and flagged if there are duplicate indication.

- CVSS / OWASP Risk Calculator<br>
Gerobug has an integrated CVSS 3.1, CVSS 4.0 and OWASP Risk Rating calculator to support the bug review process.

- Email Blacklisting<br>
Gerobug can temporarily block and release emails that conducted spam activity.

- Auto Generate Certificate<br>
We can generate certificate of appreciations for bug hunters so you don't have to ;)

- Personalization<br>
You can customize Gerobug to fit your brand colors, or pick one of seven contrast-checked theme presets.

- Troubleshooting Tools<br>
Resend a bounced email, correct report fields, pause all hunter email and read the server log from the dashboard.

- Logging and Log Rotation<br>
Gerobug have internal audit log with log rotation enabled

- Hall of Fame / Wall of fame / Leaderboard<br>
Yeah we have it too. Points are weighted by severity, and hunters can be hidden from the public page without losing their score.

<br>

## Authors
- [@VGR6479](https://github.com/VGR6479)
- [@as3ng](https://github.com/as3ng)
- [@jessicaggan](https://github.com/jessicaggan)

<br>

## Feedback
If you have any feedback, please reach out to us at __support@gerobug.com__

<br>

Copyright (c) 2025 Gero Security<br>
Licensed under the GNU AGPLv3.0 License<br>
Copyright (C) 2023-2026 the Gerobug maintainer (GitHub: @VGR6479) and Gerobug contributors.
