# Initial Access

## Public Pages

Homepage: `https://[your-domain]/`

The public pages are the **only** part of Gerobug a bug hunter needs or can reach:

* **Rules and Guidelines**: bounty terms, scope, disclosure policy and FAQ
* **Hall of Fame**: leaderboard of hunters by points (see [Hall of Fame](../hall-of-fame.md))
* **Submit Guidelines**: the program's email address and every [email command](../bug-hunter-guide.md), grouped into Report, Track, Respond, Bounty decision and Withdraw, each with its subject, body format, limits and an "Open in mail app" button

The Submit page also has a Report ID box that fills the ID into every subject
and mail button on the page. Nothing is sent or stored; the ID stays in the
hunter's browser. The mail buttons stay disabled until the program mailbox is
set up.

## Dashboard

Login page: `https://[your-domain]:6320/login` (or `http://[IP]:6320/login` without a domain).

If you answered **YES** to the VPN question during [installation](./), the dashboard is **not reachable from the internet**. Connect to your VPN first.

{% hint style="info" %}
**Still getting 403 Forbidden over the VPN?**\
The dashboard only accepts private IP ranges, but your domain resolves to the public IP. Add this line to `/etc/hosts` (Linux/macOS) or `C:\Windows\System32\drivers\etc\hosts` (Windows) on your computer:

`[INTERNAL IP]    [GEROBUG DOMAIN]`

For example: `10.0.0.1    bugbounty.example.com`. You can also open `https://[INTERNAL IP]:6320/login` directly, but the certificate will not match.
{% endhint %}

{% hint style="warning" %}
**Getting 400 Bad Request instead?** That is the host allowlist, not NGINX. The
name you used is not in `gerobug_dashboard/gerobug_host`. Add it to
`GEROBUG_ALLOWED_HOSTS` in `gerobug_dashboard/secrets/gerobug_secret.env` and
restart (see [Dashboard Host and Cookie Options](./#dashboard-host-and-cookie-options)).
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

This only works once the [mailbox is set up](../settings.md#mailbox-settings). The
reset link is built from the host allowlist, so it always points at a name you
configured, never at a forged `Host` header.
