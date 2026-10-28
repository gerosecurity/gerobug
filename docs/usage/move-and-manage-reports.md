# Move and Manage Reports

On each status, there will be slightly different action that can be done to a report.

<table><thead><tr><th>Status</th><th>Actions</th><th data-hidden></th></tr></thead><tbody><tr><td><a href="move-and-manage-reports.md#need-to-review">Need to Review</a></td><td>Mark as Invalid / Move</td><td></td></tr><tr><td><a href="move-and-manage-reports.md#in-review-fixing-retest">In Review</a></td><td>Request Amend / Move</td><td></td></tr><tr><td><a href="move-and-manage-reports.md#in-review-fixing-retest">Fixing</a></td><td>Request Amend / Move</td><td></td></tr><tr><td><a href="move-and-manage-reports.md#in-review-fixing-retest">Fixing (Retest)</a></td><td>Request Amend / Move</td><td></td></tr><tr><td><a href="move-and-manage-reports.md#bounty-calculation">Bounty Calculation</a></td><td>Send Calculation</td><td></td></tr><tr><td><a href="move-and-manage-reports.md#bounty-in-process">Bounty in Process</a></td><td>Request NDA / Complete</td><td></td></tr><tr><td><a href="move-and-manage-reports.md#complete">Complete</a></td><td>-</td><td></td></tr><tr><td>Not Valid</td><td>Delete Report</td><td></td></tr></tbody></table>

> In this current version, email templates can't be edited from the dashboard. If you want to edit the email templates, you can manually modify them at <mark style="color:red;">**gerobug\_dashboard/geromail/mail\_templates.py**</mark>

## Need to Review

This is the first status when a report is received. If the report is invalid, you can mark it as invalid and the report will be removed from the dashboard. But still accessible from the report group list.

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 4.54.50 PM.png" alt=""><figcaption><p>Mark as Invalid</p></figcaption></figure>

If the report is valid, you can move the report to the next step.

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 4.55.10 PM.png" alt=""><figcaption><p>Move Report</p></figcaption></figure>

Each time a report is moved, the bug hunter will receive email notification automatically.

<div align="left"><figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 4.58.44 PM.png" alt="" width="375"><figcaption><p>Sample Not Valid Notification to Bug Hunter</p></figcaption></figure></div>

<div align="left"><figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 4.37.00 PM.png" alt="" width="375"><figcaption><p>Sample Notification to Bug Hunter</p></figcaption></figure></div>

## In Review - Fixing (Retest)

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.04.54 PM.png" alt=""><figcaption><p>Report In Review</p></figcaption></figure>

On these phase, you can request amend (request more information / clarification to the bug hunter)

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.05.33 PM.png" alt=""><figcaption><p>Sample Request Amend</p></figcaption></figure>

The bug hunter will receive an email regarding the request and will be able to send the requested information.

<div align="left"><figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.07.38 PM.png" alt="" width="563"><figcaption><p>Sample Request Amend Notification</p></figcaption></figure></div>

After the bug hunter submitted the requested information, it will show on the report and you can access it by clicking the "View Update" button.

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.09.08 PM.png" alt=""><figcaption><p>After Bug Hunter submit the Requested Information</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.09.59 PM.png" alt=""><figcaption><p>Submitted Amend by Bug Hunter</p></figcaption></figure>

You can request more amends during 'In Review' until 'Fixing (Retest)' if necessary.

## Bounty Calculation

After the bug is fixed, you can move to this phase. In this phase, you will be able to send bounty calculation to the bug hunter depends on your company / organization policy.

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.16.21 PM.png" alt=""><figcaption><p>Report in Bounty Calculation</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.17.04 PM.png" alt=""><figcaption><p>Send Bounty Calculations</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.17.48 PM.png" alt=""><figcaption><p>Bounty Calculation on Bug Hunter</p></figcaption></figure>

The report can't be moved to the next step without agreement from the bug hunter. The bug hunter will be given a chance to appeal (3 times maximum). This is to ensure that both parties reached a mutual agreement.

If the bug hunter disagree and appeal, a button will appear and you can see the appeal details by clicking the 'View' button right beside 'Appeals'

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.20.47 PM.png" alt=""><figcaption><p>After Bug Hunter Submitted an Appeal</p></figcaption></figure>

<div align="left"><figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.21.12 PM.png" alt="" width="563"><figcaption><p>Sample Appeal by Bug Hunter</p></figcaption></figure></div>

When a bug hunter submitted an appeal, you need to reconsider and send another calculation until both parties reached a mutual agreement.

In the other hand, if the bug hunter agree to the bounty calculation, the report will be automatically moved to the next phase.

## Bounty in Process

In this phase, you can request NDA and Information from bug hunter to process the bounty according to the mutual agreement. Gerobug will send the [NDA Template](../settings.md#nda-template) to the bug hunter to be signed.

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.27.30 PM.png" alt=""><figcaption><p>Report Detail (Bounty in Process)</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.28.06 PM.png" alt=""><figcaption><p>Sample Request NDA</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.28.36 PM.png" alt=""><figcaption><p>Request NDA notification on Bug Hunter</p></figcaption></figure>

After the bug hunter submitted the NDA and requested information, it will show on the report and you can access it by clicking the "View" button right beside "Hunter Data".

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.31.57 PM.png" alt=""><figcaption><p>After Bug Hunter Submitted NDA and Data</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.34.00 PM.png" alt=""><figcaption><p>Sample NDA and Data from Bug Hunter</p></figcaption></figure>

## Complete

If all the necessary data and NDA have been received, and the bounty have been processed. You can complete the report. Gerobug will generate and send a certificate of appreciation to the bug hunter.

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.37.08 PM.png" alt=""><figcaption><p>Complete a Report</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.37.29 PM.png" alt=""><figcaption><p>Notification of Completion to Bug Hunter</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screen Shot 2023-05-17 at 5.37.49 PM.png" alt=""><figcaption><p>Sample Certificate Generated by Gerobug</p></figcaption></figure>
