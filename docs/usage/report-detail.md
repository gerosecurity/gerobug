# Report Detail

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-13 at 12.04.33 AM.png" alt=""><figcaption><p>Sample Report Detail</p></figcaption></figure>

When you click a report on the dashboard, you will see the report detail. You have options to move the report (Invalid or to the next step), and update the severity and reviewer in charge.

## Update Report Severity

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-13 at 12.05.37 AM.png" alt=""><figcaption><p>Update Report Severity</p></figcaption></figure>

You can fill the **severity string** using CVSS 3.1 or OWASP Risk format

{% hint style="info" %}
Gerobug has a built-in CVSS 3.1 and OWASP Risk Calculator to help you determine the severity of a bug and produce the severity string.
{% endhint %}

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-13 at 12.07.07 AM.png" alt=""><figcaption><p>OWASP Risk Calculator</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-13 at 12.07.44 AM.png" alt=""><figcaption><p>CVSS 3.1 Calculator</p></figcaption></figure>

Gerobug will auto calculate the severity number based on the severity string provided, and the reviewer name will be the username of the user that updated the report.

<figure><img src="../.gitbook/assets/Screen Shot 2023-08-13 at 12.09.32 AM.png" alt=""><figcaption><p>Updated Report</p></figcaption></figure>
