# Filter & Validation

Now of course you will ask, is Gerobug secure?\
Well of course the obvious answer is that **nothing is 100% secure**, lol.\
But we are confident that Gerobug is 99% secure.

We have implemented filter and validation by default to prevent security issues within Gerobug.

## Accepted Email Format

Gerobug will only accept specific email format, other than this format the report will be ignored. The bug hunter will also receive notification if the email they sent are invalid.

You can see the accepted email format at `http://[Your gerobug domain]/submit`\
which are:

*   Submit Report&#x20;

    ```
    Subject: SUBMIT_Report Title
    Body:
    TYPE= Bug Type
    ENDPOINT= Affected Endpoint
    SUMMARY= Summary

    Attachment: *PDF Report File* (Report Template)
    ```

    _<mark style="color:red;">Title -> Max 150 Characters</mark>_\
    _<mark style="color:red;">Bug Type -> Max 100 Characters</mark>_\
    _<mark style="color:red;">Endpoint -> Max 150 Characters</mark>_
*   Check Report Status&#x20;

    ```
    Subject: CHECK_Report ID
    ```
*   Check Report Status Overview

    ```
    Subject: STATUS_OVERVIEW
    ```
*   Update Report (Request Amend)

    ```
    Subject: UPDATE_Report ID
    Body:
    Summary

    Attachment: *PDF Report File*
    ```
*   Submit an Appeal

    ```
    Subject: APPEAL_Report ID
    Body:
    Reasons
    ```
*   Submit an Agree

    ```
    Subject: AGREE_Report ID
    ```
*   Submit NDA

    ```
    Subject: NDA_Report ID
    Body:
    Requested Information

    Attachment: *PDF Signed NDA File*
    ```
*   Check Score

    ```
    Subject: MY_SCORE
    ```

## Validation

Gerobug will validate files received from bug hunters, if the file is invalid (not pdf) then the report will be ignored (not saved).

<div align="left"><figure><img src=".gitbook/assets/image (9).png" alt="" width="375"><figcaption></figcaption></figure></div>

What if someone submitted a malicious PDF?\
Well since the submission is through GMAIL / OUTLOOK, malicious files are usually filtered first (Risk transfer).

## User Authorization

Bug hunter may only check, update, or do anything to their own bug reports according to the email address. For example, user1@email.com can't do anything to report ID owned by user2@email.com (vice versa).&#x20;

<div align="left"><figure><img src=".gitbook/assets/image (1).png" alt="" width="375"><figcaption></figcaption></figure></div>

Bug hunter also can't submit any update, appeal, agree, NDA without prior request from the company / organization.

## Email Blacklisting

As mentioned [before](settings.md#blacklist-rule), Gerobug able to block and release emails with spam activity.

<div align="left"><figure><img src=".gitbook/assets/image (2).png" alt="" width="375"><figcaption></figcaption></figure></div>
