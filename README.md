# Gerobug: The First Open Source Bug Bounty Platform.

![gerobugLogo](https://raw.githubusercontent.com/gerobug/gerobug-docs-images/main/logo.png)

![CodeQL](https://github.com/gerobug/gerobug/actions/workflows/github-code-scanning/codeql/badge.svg)
[![License](https://img.shields.io/badge/License-AGPLv3-red.svg?&logo=none)](https://www.gnu.org/licenses/agpl-3.0)
[![Black Hat Arsenal](https://raw.githubusercontent.com/toolswatch/badges/master/arsenal/asia/2023.svg?sanitize=true)](https://www.blackhat.com/asia-23/arsenal/schedule/index.html#gerobug-open-source-private-self-managed-bug-bounty-platform-31241)

# Gerobug
__The first open source self-managed bug bounty platform.__

Are you a company, planning to have your own bug bounty program, with minimum budget?<br>

__WE GOT YOU!__

We are aware that some organizations have had difficulty establishing their own bug bounty program.<br>
Using a third-party managed platform usually comes with a hefty price tag and security risks. _(If you know, you know...)_<br>
In the other hand, creating your own self-managed platform will take time and effort to build and maintain it.

<br>

## Why Gerobug?
- __EASY        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Have your bug bounty program running with just single line of command
- __SECURE      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Gerobug uses email parser and network segregation to minimize security risks.
- __OPEN SOURCE &nbsp;&nbsp;:__ It is FREE.

<br>

## (Minimum) Recommended Specification
* Ubuntu 20.04
* vCPU 2 Core
* RAM 2 GB
* HDD 16 GB

<br>

## Requirements
* Gmail Email with <a href="https://support.google.com/accounts/answer/185833">App password</a> implemented
* VPN Server (Recommended for Production Server)
* Domain for HTTPS (Recommended for Production Server)

__(You don't need to install anything else, we'll do it for you!)__

<br>

## Deployment and Usage
To deploy gerobug:
1. Clone this repository
```bash
git clone https://github.com/gerobug/gerobug
cd gerobug
```
2. Run the Setup Script: 
```bash
./run.sh
```
3. Follow the setup instructions (Read the [documentation](https://gerobug.gitbook.io/documentation/) for details)
4. By default, Gerobug Dashboard will listen at port __6320__

Access the login page at `http://[Internal IP]:6320/login`<br>
<br>__Credential__<br>
Username&nbsp;&nbsp;: `geromin`<br>
Password&nbsp;&nbsp;&nbsp;: Randomly generated at `gerobug/gerobug_dashboard/secrets/gerobug_secret.env`

<br>

You can read the __detailed documentation [here](https://gerobug.gitbook.io/documentation/)__

<br>

## Main Features
- Network Segregation<br>
All services are running on seperate containers. Public users only able to access the static page (Rules and guidelines).

- Easy and Quick Installation<br>
Use our run script to install Gerobug, its quick and easy!

- HTTPS Implementation<br>
Automated HTTPS configuration using NGINX and Let's Encrypt.

- Homepage<br>
This should be the only page accessible by public, which contains Rules and Guidelines for your bug bounty program.

- Email Parser<br>
Bug Hunter will submit their findings by email, which Gerobug will parse, filter, and show them on dashboard.

- Auto Reply and Notification for Bug Hunters<br>
Bug Hunter's inquiries will be automatically replied and notified if there any updates on their report.

- Notification Channel<br>
Company will also be notified via Slack/Telegram if there any new report.

- User Management<br>
Gerobug has a simple Role-based user management.

- Report Management<br>
Manage reports easily using a kanban model dashboard.

- Report Filtering and Flagging<br>
Reports from Bug Hunter will be filtered and flagged if there are duplicate indication.

- CVSS / OWASP Risk Calculator<br>
Gerobug has an integrated CVSS / OWASP Risk Calculator to support the bug review process.

- Email Blacklisting<br>
Gerobug can temporarily block and release emails that conducted spam activity.

- Auto Generate Certificate<br>
We can generate certificate of appreciations for bug hunters so you don't have to ;)

- Personalization<br>
You can customize Gerobug to fit your brand colors

- Hall of Fame / Wall of fame / Leaderboard<br>
Yeah we have it too

<br>

## Authors
- [@VGR6479](https://github.com/VGR6479)
- [@as3ng](https://github.com/as3ng)
- [@jessicaggan](https://github.com/jessicaggan)

<br>

## Feedback
If you have any feedback, please reach out to us at __gerobug.id@gmail.com__

