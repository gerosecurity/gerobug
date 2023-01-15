# Gerobug
![gerobugLogo](https://raw.githubusercontent.com/gerobug/gerobug-docs-images/main/logo.png)

Open source private (self-managed) bug bounty platform.

Are you a company, planning to have your own bug bounty program, with minimum budget? __We got you!__

We are aware that some organizations have had difficulty establishing their own bug bounty program. <br>
If you know what you're doing, using a third-party managed platform usually comes with a hefty price tag and increased security concerns.
<br>
However, creating your own independently run platform will take time and effort.


## Why Gerobug?
- __Easy:__ Have your bug bounty program running with just single line of command
- __Secure:__ Gerobug use email parser to receive reports to minimize security risks
- __Open Source:__ It is FREE.


## Requirements
* Gmail Email with <a href="https://support.google.com/accounts/answer/185833">App password</a> implemented
* Docker
* Docker-compose
* Python 3.8


## Deployment and Usage
To deploy gerobug:
1. Clone this repository
2. Run this: 
```bash
sudo docker-compose up --build --force-recreate -d
```
3. By default Gerobug will listen on port 6320

You can read the __detailed documentation [here](https://bit.ly/GerobugDocumentation)__
If you need to see the UML diagrams, you can see them [here] (https://drive.google.com/drive/folders/1eYKZLc_nQY2bv_Byak60WVrMSbaHTeUM?usp=sharing)__

## Main Features
- Homepage<br>
This should be the only page accessible by public, which contains Rules and Guidelines for your bug bounty program.

- Email Parser<br>
Bug Hunter will submit their findings by email, which Gerobug will parse, filter, and show them on dashboard.

- Auto Reply and Notification<br>
Bug Hunter's inquiries will be automatically replied and notified if there any updates on their report.<br>
Company will also be notified via Slack if there any new report.

- Report Management<br>
Manage reports easily using a kanban model.

- Report Filtering and Flagging<br>
Reports from Bug Hunter will be filtered and flagged if there are duplicate indication.

- Email Blacklisting<br>
Gerobug can temporarily block and release emails that conducted spam activity

- Auto Generate Certificate<br>
We can generate certificate of appreciations for bug hunters so you don't have to ;)

- Hall of Fame / Wall of fame / Leaderboard<br>
Yeah we have it too


## TODO
- [ ] Feature for Bug Hunter to Check All His/Her Report Status (Overview)
- [ ] Improve Notifications and Confirmations (Mailbox Active/Invalid, Email Sent to Bug Hunter, Current Mailbox, etc.)
- [ ] Implement Global Dynamic Variables (Email, URL)
- [ ] Add Email Template Setting
- [ ] Add Support for Other Mailboxes (Outlook, Apple, etc.)
- [ ] Add Integrated CVSS/OWASP Risk Calculator
- [ ] Add Forced Prompt to Change Default Password and Setup Mailbox
- [ ] Add RBAC for Admin Users
- [ ] Add More Settings for Admin (Slack Webhooks)
- [ ] Add Flow Control (Custom Status, Add / Remove Status)
- [ ] Improve Duplicate Detection Algorithm
- [ ] Improve Backend Performance and Efficiency
- [ ] Improve Logging Module
- [ ] Split Homepage and Dashboard Endpoint
- [ ] Split Dashboard and Parser (API)


## Authors
- [@VGR6479](https://github.com/VGR6479)
- [@as3ng](https://github.com/as3ng)
- [@jessicaggan](https://github.com/jessicaggan)


## Feedback
If you have any feedback, please reach out to us at gerobug.id@gmail.com

