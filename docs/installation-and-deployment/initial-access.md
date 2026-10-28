# Initial Access

## Public Pages

Homepage: `https://[your-domain]/`

The public pages are the **only** part of Gerobug a bug hunter needs or can reach:

* **Rules and Guidelines**: bounty terms, scope, disclosure policy and FAQ
* **Hall of Fame**: leaderboard of hunters by points
* **Submit Guidelines**: the program's email address and the [email commands](../bug-hunter-guide.md)

## Dashboard

Login page: `https://[your-domain]:6320/login` (or `http://[IP]:6320/login` without a domain).

If you answered **YES** to the VPN question during [installation](./), the dashboard is **not reachable from the internet**. Connect to your VPN first.

{% hint style="info" %}
**Still getting 403 Forbidden over the VPN?**\
The dashboard only accepts private IP ranges, but your domain resolves to the public IP. Add this line to `/etc/hosts` (Linux/macOS) or `C:\Windows\System32\drivers\etc\hosts` (Windows) on your computer:

`[INTERNAL IP]    [GEROBUG DOMAIN]`

For example: `10.0.0.1    bugbounty.example.com`. You can also open `https://[INTERNAL IP]:6320/login` directly, but the certificate will not match.
{% endhint %}

## First Login

| | |
| --- | --- |
| Username | `geromin` |
| Password | Randomly generated, stored in `gerobug_dashboard/secrets/gerobug_secret.env` (`DJANGO_SUPERUSER_PASSWORD`) |

```bash
cat gerobug_dashboard/secrets/gerobug_secret.env
```

After logging in, go to [Settings](../settings.md) and configure the mailbox first. Gerobug cannot receive reports or send emails until the mailbox is active.

After login you land on the [Kanban dashboard](../usage/).

## Forgot Password

The login page has a **Forgot Password** link. Enter the account's email address and Gerobug emails a reset link. New reviewers receive the same kind of link when their account is created.

This only works once the [mailbox is set up](../settings.md#mailbox-settings).
