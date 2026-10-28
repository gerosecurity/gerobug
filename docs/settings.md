# Settings

**The setting page is only accessible by admin.**

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 3.33.06 PM.png" alt=""><figcaption><p>Admin Setting Page</p></figcaption></figure>

## Mailbox Settings

Gerobug need a GMAIL Email with [App Password](https://support.google.com/accounts/answer/185833?hl=en) implemented. Without this, Gerobug can not receive any reports submitted by the bug hunter. It is **RECOMMENDED** to use a **dedicated email** for this. Do not use the mailbox email for other purposes to avoid issues / conflicts during the parsing process.

<div align="left"><figure><img src=".gitbook/assets/Screenshot 2024-04-14 at 02.44.41.png" alt=""><figcaption><p>Sample Configured Mailbox</p></figcaption></figure></div>

If the email is configured successfully, you will see that the email is **ACTIVE**, and Gerobug will able to receive bug reports and send emails.

<figure><img src=".gitbook/assets/Screenshot 2024-04-14 at 02.46.01.png" alt=""><figcaption><p>Submission Guideline Page will be Updated Automatically</p></figcaption></figure>

## User Account Settings

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 3.41.58 PM.png" alt=""><figcaption><p>User Account Setting</p></figcaption></figure>

You can change user email and password from this setting.

## Personalization

<figure><img src=".gitbook/assets/Screenshot 2024-04-14 at 02.47.04.png" alt=""><figcaption><p>Personalization Setting</p></figcaption></figure>

You can change the Gerobug logo to your own company/organization logo&#x20;

(Will affect the homepage and certificate generated)

## Edit Rules and Guidelines

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 3.47.57 PM.png" alt=""><figcaption><p>Edit Rules and Guidelines</p></figcaption></figure>

You can change the rules and guidelines for your bug bounty program.

## Manage Roles

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 3.50.41 PM.png" alt=""><figcaption><p>Manage Roles</p></figcaption></figure>

Admin can create and delete users with lesser privilege (Reviewer). These users can be used to manage bug reports (Review and Triage) without having the permission to access the setting page.

The default password for the reviewer users are <mark style="color:red;">`G3r0bUg_@dM!n_1337yipPie13579246810121337`</mark>&#x20;

Each users can reset the password using the forgot password feature.&#x20;

{% hint style="info" %}
Please enforce the users to change the default password to minimize security risks!
{% endhint %}

## Notification Channels

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 3.55.54 PM.png" alt=""><figcaption><p>Notification Channels</p></figcaption></figure>

Gerobug support Slack and Telegram as notification channels, which Gerobug will send notification when there are new reports.

### [Slack Webhook](https://api.slack.com/messaging/webhooks)

Format: https://hooks.slack.com/services/<mark style="color:orange;">T00000000</mark>/<mark style="color:orange;">B00000000</mark>/<mark style="color:orange;">XXXXXXXXXXXXXXXXXXXXXXXX</mark>

![](<.gitbook/assets/Screen Shot 2023-05-17 at 4.07.31 PM.png>)

### [Telegram Webhook](https://core.telegram.org/bots)

Format: https://api.telegram.org/bot<mark style="color:blue;">\<token></mark>/sendMessage?chat\_id=<mark style="color:blue;">\<channel\_id></mark>

![](<.gitbook/assets/Screen Shot 2023-05-17 at 4.08.36 PM.png>)

## Blacklist Rule

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 4.14.00 PM.png" alt=""><figcaption><p>Blacklist Rule Setting</p></figcaption></figure>

Gerobug is equipped with Blacklist Rule (a simple rate limit) to block any email address that conducted Spam.

## Report Template

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 4.16.05 PM.png" alt=""><figcaption><p>Report Template Setting</p></figcaption></figure>

You can set report template (PDF) for bug hunters, which they can download at the Rules and Guidelines Page.



## NDA Template

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 4.16.19 PM.png" alt=""><figcaption><p>NDA Template Setting</p></figcaption></figure>

You can set NDA template (PDF) for bug hunters, which will be sent to bug hunters before the bounty is processed.



## Certificate Template

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 4.19.38 PM.png" alt=""><figcaption><p>Certificate Template</p></figcaption></figure>

Gerobug will generate and send certificate of appreciation to bug hunter automatically when a report is fixed and completed.

You can update the certificate template (JPG) to your own design, but we **do not recommend** it since it may broke the generated certificate due to different sizing and positioning.&#x20;

```
Our certificate template
Dimensions: 3508 × 2480
Resolution: 300x300
```

We will produce more certificate template options in the future.

You can also change the data (Officer name, signature, and title) and generate a sample certificate.

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 4.22.21 PM.png" alt=""><figcaption><p>Sample Certificate</p></figcaption></figure>

