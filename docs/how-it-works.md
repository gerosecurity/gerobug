# How it works?

## Architecture

<figure><img src=".gitbook/assets/Architecture Diagram (Gerobug v2.1).png" alt=""><figcaption><p>Architecture Diagram</p></figcaption></figure>

Gerobug runs as four Docker containers, started with `docker compose`:

| Container | Role | Exposure |
| --- | --- | --- |
| `nginx` | Reverse proxy, HTTPS termination | Ports 80, 443 (public pages) and 6320 (dashboard) |
| `web` | Public pages: Rules and Guidelines, Submit Guidelines, Hall of Fame | Through NGINX only |
| `dashboard` | Admin/Reviewer dashboard and the email parser (Geroparser) | Through NGINX port 6320 only |
| `db` | PostgreSQL 17 | Internal network only |

When you answer **YES** to the VPN question during installation, NGINX only accepts dashboard connections (port 6320) from loopback and private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), so staff reach it over your VPN.

## Company

Any company or organization that wants to run a bug bounty program clones Gerobug and deploys it on its own server. Unlike HackerOne, Bugcrowd or YesWeHack, Gerobug is **self-managed**: your reports and data never leave your infrastructure.

## Bug Hunter

Bug hunters do not register or log in. They can only see the public pages: Rules and Guidelines, Submit Guidelines and Hall of Fame.

All reports and follow-ups are sent **by email** to the program mailbox. Gerobug filters and parses them and shows them on the dashboard. This keeps the attack surface small: Gerobug stores no hunter credentials (no account takeover or credential leak), and there is no web upload form (no direct path for malicious uploads). See [Bug Hunter Guide](bug-hunter-guide.md) for every command a hunter can send.

## Email Parser (Geroparser)

Geroparser runs inside the `dashboard` container. It:

1. Waits until a mailbox is configured in [Settings](settings.md#mailbox-settings).
2. Connects to the mailbox over IMAP (SSL) and polls the **inbox every 30 seconds**. The spam/junk folder is also scanned periodically, so reports caught by the mail provider's spam filter are not lost.
3. Reconnects automatically every 3 hours, or as soon as the connection drops. A supervisor restarts the parser with exponential backoff (up to 5 minutes) if it crashes.
4. Checks every 30 seconds for bounty calculations whose 30-day appeal window has expired (see [Bounty Calculation](usage/move-and-manage-reports.md#bounty-calculation-and-appeals)).

## Report Lifecycle

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 2.41.48 PM.png" alt=""><figcaption><p>Default Bug Bounty Flow</p></figcaption></figure>

Every report moves through these statuses:

| ID | Status | What happens | Hunter may |
| --- | --- | --- | --- |
| 0 | Not Valid | Rejected by a reviewer (optionally as a duplicate of another report) | Nothing |
| 1 | Need to Review | New report received | Send updates |
| 2 | In Review | Being triaged | Send updates |
| 3 | Fixing | Accepted, waiting for a fix | Send updates |
| 4 | Fixing (Retest) | Fix being verified | Send updates |
| 5 | Bounty Calculation | Bounty calculation sent to the hunter | Send updates, appeal or agree |
| 6 | Bounty in Process | Bounty agreed; prerequisites/NDA collected | Send requested data / NDA |
| 7 | Completed | Bounty paid, certificate sent | Nothing |

Hunter permissions are enforced per report and are reset automatically whenever the status changes, so a hunter can never act on a stage the report has already left.

{% hint style="info" %}
The flow is fixed. Custom statuses cannot be added or removed in the current version.
{% endhint %}
