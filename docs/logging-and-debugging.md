# Logging & Debugging

## Container Logs

```bash
cd gerobug
docker compose logs -f
```

To follow only the dashboard and parser:

```bash
docker compose logs -f dashboard
```

## Gerobug Log

The application log is written to `log/gerobug.log` in the Gerobug folder. It rotates at midnight and keeps 31 days. Admins can also read it in the dashboard under [Settings > Troubleshooting > Server Logs](troubleshooting.md#server-logs).

### Startup

`Waiting for Mailbox Setup...` means the mailbox must be configured before Gerobug can receive reports. Once it connects you will see `Geroparser connected to mailbox.`

### Incoming Email

Each processed email is logged between `====` lines with time, sender, subject and the result code:

| Code | Meaning |
| --- | --- |
| `[CODE 201]` | Report saved |
| `[CODE 202]` | Status check |
| `[CODE 203]` | Update saved |
| `[CODE 204]` | Appeal saved |
| `[CODE 205]` | Agreement saved |
| `[CODE 206]` | Data/NDA saved |
| `[CODE 207]` | Score check |
| `[CODE 208]` | Status overview |
| `[ERROR 403]` | Hunter not authorized |
| `[ERROR 404]` | Invalid format, missing PDF, or fields too short/long |
| `[ERROR 405]` | Unknown Report ID |
| `[ERROR 407]` | Self-update allowance used up |
| `[ERROR 408]` | Updates closed for this stage |
| `[ERROR 409]` | Appeal limit reached |
| `[AUTO-AGREE]` | Bounty calculation accepted after 30 days |

`Permission = ...` lines show how Gerobug validates hunter authorization (similar to RWX on Linux: 4 Update, 2 Appeal, 1 NDA).

### Ignored Email

| Log message | Reason |
| --- | --- |
| `Possible Spoofing Attempt ...` / SPF and DKIM failure | Sender failed authentication |
| `No-reply emails, Ignoring Mail!` | No-reply sender |
| `Self Email` / `Automated sender` / `Own-domain sender (loop guard)` | Mail-loop protection |
| `EMAIL DELIVERY FAILED ...` | A bounce for an email Gerobug sent |
| Blacklist messages | Sender rate-limited |

### Outgoing Email

`Sent Email Successfully | To: ... | ReportID: ... | Template: ...` confirms delivery to the SMTP server. `SUPPRESSED by sinkhole` means the [Hunter Email Sinkhole](troubleshooting.md#hunter-email-sinkhole) is on.

### Dashboard Actions

Status changes, severity updates, overrides, user management and settings changes are logged with the username that performed them.
