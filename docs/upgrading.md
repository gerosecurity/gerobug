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

### v3.1

* **Theme colors.** An installation still using the original (pre-3.1) default colors is moved to the new Gero Dark defaults on first boot. If you customized any color, nothing changes; the original look is available as the **Gero Classic** preset.
* **Submission guidelines.** New installs ask hunters to share videos, archives and exploit code as links inside the PDF. Existing installs keep their saved rules; paste the bullet into **Settings > Rules** if you want it.
* **Auto-accept.** Reports already at Bounty Calculation before the upgrade never auto-accept, because their hunters were not told about the 30-day window. Resend the calculation (from the report page or **Troubleshooting > Resend Email**) to start the window.
* **Resend Email** only knows about emails sent after the upgrade.
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
