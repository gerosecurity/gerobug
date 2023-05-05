![djangoTest](https://github.com/gerobug/gerobug/actions/workflows/django.yml/badge.svg)

# Gerobug
![gerobugLogo](https://raw.githubusercontent.com/gerobug/gerobug-docs-images/main/logo.png)

__Open source private (Self-managed) bug bounty platform.__

Are you a company, planning to have your own bug bounty program, with minimum budget? 🤔<br>

__WE GOT YOU! 🫵__

We are aware that some organizations have had difficulty establishing their own bug bounty program. 😰<br>
Using a third-party managed platform usually comes with a hefty price tag and security risks. 🙊 _(If you know, you know...)_<br>
In the other hand, creating your own self-managed platform will take time and effort to build and maintain it. 😓

<br>

## Why Gerobug?
- __EASY        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Have your bug bounty program running with just single line of command 😏
- __SECURE      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:__ Gerobug use email parser to receive reports to minimize security risks 🦾
- __OPEN SOURCE &nbsp;&nbsp;&nbsp;&nbsp;:__ It is FREE. 🤩

<br>

## Requirements
* Gmail Email with <a href="https://support.google.com/accounts/answer/185833">App password</a> implemented
* Docker (Latest)
* Docker-compose (Latest)
* Python 3.8 or above

<br>

## Deployment and Usage
__[This Version is Not Ready for Production Yet, We Will Update it ASAP]__<br><br>
To deploy gerobug:
1. Clone this repository
```bash
git clone https://github.com/gerobug/gerobug
```
2. Run this: 
```bash
sudo docker-compose up --build --force-recreate -d
```
3. By default Gerobug will listen on port 6320
4. Setup Mailbox and Change Admin Password

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

<br>

## NOTE
Currently we are not accepting any bug issues, since we're still actively maintain and improving its features and capabilities. But we are open to any feedbacks and suggestions. Thank you for your understanding. 🙏

<br>

## ON GOING IMPROVEMENTS
- [ ] Completely Seperate "Rules & Guidelines" Page from Dashboard and DB (Air Gap)
- [ ] Add Capability to Edit Report and NDA Template on Admin Setting
- [ ] Add Capability to Edit Certificate Template on Admin Setting
- [ ] Add Forced Prompt to Change Default Password and Setup Mailbox
- [ ] Add Capability to Edit Email Template on Admin Setting
- [ ] Add Support for Other Mailboxes (Outlook, Apple, etc.)
- [ ] Add Flow Control (Custom Status, Add / Remove Status)
- [ ] Auto Calculate Severity String to Number Format
- [ ] Improve Dockerization
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

