# Installation & Deployment

## Requirements

* A **dedicated** mailbox for the program:
  * Gmail with an [App Password](https://support.google.com/accounts/answer/185833), or
  * Outlook with an [App Password](https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944), or
  * Any other provider with IMAP (SSL) and SMTP access (Custom)
* Open ports **80**, **443** and **6320**
* VPN server and private subnet (recommended for production)
* Domain name for HTTPS (recommended for production)

The installer installs Docker, Docker Compose v2, Python 3 and the other prerequisites for you.

## (Minimum) Recommended Specification

* Ubuntu 24.04
* 2 vCPU
* 2 GB RAM
* 16 GB disk

Size up depending on your organization and expected report volume.

## Deployment

1. Clone the repository

   ```bash
   git clone https://github.com/gerosecurity/gerobug
   cd gerobug
   ```

2. Run the setup script (as a user with `sudo` rights)

   ```bash
   ./gerobug.sh
   ```

   The script offers five actions:

   ```
   1) INSTALL
   2) UPDATE
   3) RESTART
   4) RENEW SSL
   5) EXIT
   ```

   Choose **1) INSTALL**.

3. Answer the setup questions

   1. **Public IP.** Gerobug detects the server's primary IP. Confirm it or enter another one.
   2. **Internal IP.** Confirm the detected internal IP or enter another one. If not applicable, enter `127.0.0.1`.
   3. **Domain.** Choose YES and enter your domain (for example `bugbounty.example.com`) to enable HTTPS. Gerobug obtains a Let's Encrypt certificate with Certbot. Make sure the domain already points to the server and port 80 is reachable.
      * You are then asked whether to **auto-renew** the certificate. YES adds a monthly cron job (`cron/renew_certbot.sh`, logs in `log/renew_certbot.log`) that renews the certificate and reloads NGINX.
      * If you have no domain, Gerobug runs over plain HTTP. **Not recommended for production.** Run the script again later to add HTTPS.
   4. **VPN.** Choose YES if you have a VPN server and private subnet. The dashboard will then only accept connections from internal IP ranges, so staff must connect through the VPN. Choosing NO exposes the dashboard publicly. **Not recommended for production.**

4. Gerobug finishes the installation

   The script installs prerequisites, generates the secrets, builds the containers and opens the log viewer (`VIEWING GEROBUG LOG`). Wait until the `dashboard` and `web` containers are running. Press `Ctrl+C` to leave the log viewer; Gerobug keeps running.

   To view the logs again, run `docker compose logs -f` in the Gerobug folder.

{% hint style="info" %}
The whole installation takes around 5-15 minutes.

The dashboard listens on port **6320**. The login page is at `https://[your-domain]:6320/login` (or `http://[IP]:6320/login` without a domain).
{% endhint %}

Next: [Initial Access](initial-access.md).

## Generated Secrets

The installer creates these files once and never overwrites them:

| File | Content |
| --- | --- |
| `gerobug_dashboard/secrets/db_secret.env` | PostgreSQL password |
| `gerobug_dashboard/secrets/gerobug_secret.env` | Admin password and `FIELD_ENCRYPTION_KEY` |

{% hint style="danger" %}
Back up the `secrets` folder. `FIELD_ENCRYPTION_KEY` encrypts the stored mailbox password and webhook URLs. If it is lost, those values cannot be decrypted and must be entered again.
{% endhint %}

## Data Locations

| Path | Content |
| --- | --- |
| `db_data/` | PostgreSQL data |
| `log/` | `gerobug.log` (rotated daily, 31 days kept) |
| Inside the `dashboard` container: `/src/report_files` | Report, update, appeal and NDA PDFs |

## Other Script Actions

* **2) UPDATE** pulls the latest `main` branch, backs up the logo, templates, report files and host settings from the running container, then rebuilds. See [Upgrading](../upgrading.md).
* **3) RESTART** stops and rebuilds the containers.
* **4) RENEW SSL** renews the Let's Encrypt certificate manually and reloads NGINX.
