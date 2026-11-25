# Upgrading

## Update Gerobug

```bash
cd gerobug
./gerobug.sh
# choose 2) UPDATE
```

The updater:

1. Pulls the latest `main` branch.
2. Copies the logo, templates, report files and host settings out of the running `dashboard` container.
3. Rebuilds and restarts the containers. Database migrations run automatically on startup.
4. Refreshes the sample files.

Your database (`db_data/`), secrets and logs stay in place.

{% hint style="warning" %}
Back up `db_data/`, `gerobug_dashboard/secrets/` and the report files before upgrading a production instance.
{% endhint %}

## Upgrade Notes

### v4.0

#### Hall of Fame is rescored once

Points are now the severity score, rounded down, times a band weight (Low 1,
Medium 2, High 3, Critical 4). On first boot **every hunter's score is
recomputed once from their completed reports**. That replaces any manual score
correction previously made, and it will change existing totals, because the old
scoring added the severity score alone.

Two new fields support it: `report_score_awarded` on a report (the points that
report currently contributes) and `hunter_hidden` on a bug hunter. Completed
reports are back-filled with the points they awarded, so a later move out of
Completed subtracts the right amount. If a score still looks wrong, correct it
with **Recompute** in Settings > Troubleshooting > Hall of Fame.

#### Host allowlist can return HTTP 400

`ALLOWED_HOSTS` used to be `*`, so a forged `Host` header could end up in a
password reset link. The dashboard now accepts only `127.0.0.1`, `localhost` and
the names in `gerobug_dashboard/gerobug_host`.

An install reached by a name that is not in `gerobug_host` (for example a public
IP behind NAT, or an extra DNS alias) now gets **HTTP 400**. Add the extra names,
separated by commas, to the dashboard's env file and restart:

```
GEROBUG_ALLOWED_HOSTS=bugbounty.example.com,203.0.113.7
```

in `gerobug_dashboard/secrets/gerobug_secret.env`, which is the dashboard
container's `env_file`. It is not read from a root `.env`.

#### Optional secure cookies

For a dashboard served over HTTPS, set `GEROBUG_SECURE_COOKIES=true` in the same
file and recreate the dashboard container. Both the session and the CSRF cookie
then require HTTPS. The default stays `false` for the documented local HTTP
tunnel.

{% hint style="warning" %}
Do not enable it on an HTTP-only route: browsers will stop sending the session
and CSRF cookies and nobody can log in. No forwarded-protocol header is trusted
by this option.
{% endhint %}

#### Other v4.0 notes

* **New tables:** `ProcessedMail` (inbound deduplication by `Message-ID`, swept
  after 180 days) and `BugReportHunterComment` (hunter questions).
* **New fields on a report:** `report_status_changed_at`,
  `report_hunter_comment`, `report_calc_sent_at`, `report_reminder_sent_at`.
* Reports that existed before the upgrade show no "since" date on their status
  card until their stage next changes.
* **Settings > Rules** text saved before the upgrade keeps whatever command list
  it contained until you edit it. The eleven commands are documented on the
  public Submit page automatically, so you no longer need to list them there.
  Paste the bullet about sharing videos, archives and exploit code as links
  inside the PDF if you want it, and tell hunters about the message size limits.
* **New report IDs are random hex.** Existing report IDs keep working.
* `MY_SCORE` and `STATUS_OVERVIEW` from a sender with no reports changed from an
  authorization failure to a "No Reports Yet" reply.
* A bounty decision still needs an explicit `AGREE_` or `APPEAL_`. A plain reply
  to the decision email is not treated as agreement.
* Reports already at Bounty Calculation before the upgrade never auto-accept,
  because their hunters were not told about the 30-day window. Send the
  calculation again from the report page to start it.
* **Resend Email** only knows about emails sent after the upgrade, and resending
  a bounty calculation does not restart the auto-accept countdown.
* Report titles stored with line breaks from folded subjects are unfolded once on
  first boot.
* Existing stored attachments are not retrospectively repaired.

### v3.1

* **Theme colors.** An installation still using the original (pre-3.1) default colors is moved to the new Gero Dark defaults on first boot. If you customized any color, nothing changes; the original look is available as the **Gero Classic** preset.
* **Spoofing protection** now relies on the mail provider's `Authentication-Results` header. Make sure your provider adds it.

### v3.0

* Mailbox passwords and webhook URLs are encrypted with `FIELD_ENCRYPTION_KEY`, which the installer adds to `gerobug_secret.env`. Back it up.
* New reviewers no longer get a shared default password; they receive a password reset link.

## Renew the SSL Certificate

```bash
./gerobug.sh
# choose 4) RENEW SSL
```

If you enabled auto-renew during installation, a monthly cron job does this and reloads NGINX automatically.
