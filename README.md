![CodeQL](https://github.com/gerobug/gerobug/actions/workflows/github-code-scanning/codeql/badge.svg)

# Gerobug
![gerobugLogo](https://raw.githubusercontent.com/gerobug/gerobug-docs-images/main/logo.png)

__The first open source self-managed bug bounty platform.__

Are you a company, planning to have your own bug bounty program, with minimum budget? 🤔<br>

__WE GOT YOU! 🫵__

We are aware that some organizations have had difficulty establishing their own bug bounty program. 😰<br>
Using a third-party managed platform usually comes with a hefty price tag and security risks. 🙊 _(If you know, you know...)_<br>
In the other hand, creating your own self-managed platform will take time and effort to build and maintain it. 😓

<br>

## Why Gerobug?
- __EASY        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Have your bug bounty program running with just single line of command 😏
- __SECURE      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Gerobug uses email parser and network segregation to minimize security risks. 🦾
- __OPEN SOURCE &nbsp;&nbsp;:__ It is FREE. 🤩

<br>

## Bare Minimum Specification
* Ubuntu 18.04
* vCPU 1 Core
* RAM 1 GB
* HDD 10 GB

<br>

## Requirements
* Gmail Email with <a href="https://support.google.com/accounts/answer/185833">App password</a> implemented
* Docker (Latest)
* Docker-compose (Latest)
* Python 3.8 or above

__(You don't need to install it manually, we'll do it for you!)__

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
3. Follow the setup instructions (Make sure the __Allowed Host__ is set to your __STATIC INTERNAL IP__)
4. By default, Gerobug Dashboard will listen at port __6320__ (Access the login page at __http://[Internal IP]:6320/login__)

<br>

You can read the __detailed documentation [here](https://bit.ly/GerobugDocumentation)__ 
<br>
If you need to see the UML diagrams, you can see them __[here](https://drive.google.com/drive/folders/1eYKZLc_nQY2bv_Byak60WVrMSbaHTeUM)__

<br>

## Main Features
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
Manage reports easily using a kanban model.

- Report Filtering and Flagging<br>
Reports from Bug Hunter will be filtered and flagged if there are duplicate indication.

- OWASP Risk Calculator<br>
Gerobug has an integrated OWASP Risk Calculator to support the bug review process.

- Email Blacklisting<br>
Gerobug can temporarily block and release emails that conducted spam activity.

- Auto Generate Certificate<br>
We can generate certificate of appreciations for bug hunters so you don't have to ;)

- Hall of Fame / Wall of fame / Leaderboard<br>
Yeah we have it too

- Network Segregation<br>
All services are running on seperate containers. Public users only able to access the static page (Rules and guidelines).

<br>

## NOTE
Currently we are not accepting any bug issues, since we're still actively maintain and improving its features and capabilities. But we are open to any feedbacks and suggestions. Thank you for your understanding. 🙏

<br>

## ON GOING IMPROVEMENTS
- [ ] Add Capability to Edit Email Template on Admin Setting
- [ ] Add Support for Other Mailboxes (Outlook, Apple, etc.)
- [ ] Add Flow Control (Custom Status, Add / Remove Status)
- [ ] Auto Calculate Severity String to Number Format
- [ ] Improve RBAC for Reviewer Users (Assign and Link Reports)
- [ ] Improve Notifications and Confirmations on Successful Actions 
- [ ] Improve Duplicate Detection Algorithm
- [ ] Improve Logging Module
- [ ] Improve Backend Performance and Efficiency
- [ ] And many more... 🥵

<br>

## Authors
- [@VGR6479](https://github.com/VGR6479)
- [@as3ng](https://github.com/as3ng)
- [@jessicaggan](https://github.com/jessicaggan)

<br>

## Feedback
If you have any feedback, please reach out to us at __gerobug.id@gmail.com__ 🫶

