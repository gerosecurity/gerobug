# Initial Access

## Accessing the Homepage

Homepage: `https://[Your Gerobug Domain]/`

The homepage should be **the only page** that is **needed** and **accessible** by the **Bug Hunter**. They can read and get to know about the bug bounty program rules and guidelines, access the hall of fame, and get comprehensive instructions on how to submit or follow up on their report(s).

<figure><img src="../.gitbook/assets/Screenshot 2024-04-14 at 02.34.32.png" alt=""><figcaption><p>Rules and Guidelines Page</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screenshot 2024-04-14 at 02.36.37 (1).png" alt=""><figcaption><p>Hall of Fame Page</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screenshot 2024-04-14 at 02.37.03.png" alt=""><figcaption><p>Submission Guidelines Page</p></figcaption></figure>

## Accessing the Dashboard

Dashboard Login Page: `https://[Your Gerobug Domain]:6320/login`

If you chose **YES** on having a VPN Server within the [installation](./) process, the Gerobug dashboard will **not accessible by public**

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.46.20 PM.png" alt=""><figcaption><p><strong>You need to connect to your VPN Server on the same network of Gerobug Server to access the dashboard.</strong> </p></figcaption></figure>

**IMPORTANT**\
If you still receive 403 Forbidden even after using the VPN, you should add

`[INTERNAL IP]                         [GEROBUG DOMAIN]`

at `/etc/hosts` (Linux / MacOS) or _`C:\Windows\System32\drivers\etc\hosts`_ (Windows) \
on your local computer before accessing the dashboard.

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.36.29 PM.png" alt=""><figcaption><p>For example, adding this line to /etc/hosts<br><strong>10.0.0.1                            demo.gerobug.com</strong></p></figcaption></figure>

{% hint style="info" %}
**Why tho?**\
Because Gerobug Dashboard only accepts connection from internal IP, so we need to define on our host file to connect using our VPN internal IP instead of public IP\
\
or you can simply access Gerobug Dashboard from\
`https://[INTERNAL IP]:6320/login`\
(But the HTTPS won't work since it requires a Domain instead of IP Address)
{% endhint %}



<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 3.14.14 PM.png" alt=""><figcaption><p>Gerobug Dashboard Login Page</p></figcaption></figure>

**Default Admin Credentials**

Username: `geromin`

Password will be randomly generated, check it on the initiation log

<div align="left"><figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 3.19.36 PM.png" alt="" width="375"><figcaption><p>Password on the Initiation Log</p></figcaption></figure></div>

or check the password manually:&#x20;

`cat gerobug/gerobug_dashboard/secrets/gerobug_secret.env`



This will be the main dashboard where reports will be shown as Kanban Board.&#x20;

<figure><img src="../.gitbook/assets/Screenshot 2024-04-14 at 02.41.27 (1).png" alt=""><figcaption><p>Gerobug Dashboard</p></figcaption></figure>

{% hint style="info" %}
’Bounty Preparation’ column contains both ‘Bounty Calculation’ and ‘Bounty in Process’
{% endhint %}

_In this current version, you cannot add or remove columns_



## Forgot Password

<figure><img src="../.gitbook/assets/image (8).png" alt=""><figcaption><p>Forgot Password Page</p></figcaption></figure>

<div align="left"><figure><img src="../.gitbook/assets/image.png" alt="" width="360"><figcaption><p>Sample Forgot Password Email</p></figcaption></figure></div>

Forgot password functionality allows users to reset their password if they have forgotten it. This is accomplished by having the user enter their email address or username associated with the account, then sending them a link or code to reset their password. The link or code is sent via email. Once the user has clicked the link or entered the code, they will be prompted to create a new password. This process is designed to ensure that only the rightful owner of the account can reset the password.

Keep in mind that this feature will only work properly after the [mailbox being setup](../settings.md#mailbox-settings).

