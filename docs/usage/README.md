# Usage

Once the [mailbox](../settings.md#mailbox-settings) is active, Gerobug starts receiving reports from bug hunters.

## Dashboard

The dashboard is a Kanban board with one column per active status (Need to Review, In Review, Fixing, Fixing (Retest), Bounty Calculation, Bounty in Process). Each card shows the Report ID, title, hunter and severity name (Informational, Low, Medium, High, Critical).

* **Drag and drop** a card to another column to change its status. The hunter receives the same status-change email as when using the forward button.
* **Search** by Report ID, title or hunter, and **filter** by severity.
* The highest-severity report is sorted to the top of each column.
* **Aging badge.** Cards older than 7 days show their age; older than 14 days they are highlighted.
* **Duplicate badge.** A warning on a card means it may duplicate an earlier report. Duplicate detection ignores differences in scheme, host case, `www.`, trailing slash, query string and fragment, and compares attack types without case or spacing. It is advisory: always verify manually.
* **Auto-accept countdown** on reports waiting at Bounty Calculation.

Reports can also be listed per status, including Not Valid and Completed.

{% hint style="info" %}
Status changes and emails to hunters are disabled while the mailbox is not active.
{% endhint %}

See [Report Detail](report-detail.md) and [Move and Manage Reports](move-and-manage-reports.md).

## Hunter Updates

Hunters may send **3 updates on their own initiative** per report. Updates you request with Request Amend are free and do not count. Updates are accepted until the report leaves Bounty Calculation; after that, hunters get an "updates closed" reply naming the current stage.
