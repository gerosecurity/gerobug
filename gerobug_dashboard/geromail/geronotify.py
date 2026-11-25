import requests
import json
import logging
from urllib.parse import quote
from prerequisites.models import Webhook


# ACTION -> (HEADER, FIRST-LINE LABEL, TRAILING NOTE)
_MESSAGES = {
    "NEW_REPORT": ("NEW REPORT RECEIVED", "Title", ""),
    "NEW_UPDATE": ("NEW UPDATE/AMEND RECEIVED", "Report ID", ""),
    "NEW_APPEAL": ("NEW APPEAL RECEIVED", "Report ID", ""),
    "NEW_AGREE": ("HUNTER AGREEMENT RECEIVED", "Report ID",
                  "\nReport will be automatically moved to the next phase."),
    "NEW_NDA": ("NEW NDA SUBMISSION RECEIVED", "Report ID", ""),
    "NEW_COMMENT": ("NEW HUNTER COMMENT RECEIVED", "Report ID", ""),
    "REPORT_WITHDRAWN": ("REPORT WITHDRAWN BY HUNTER", "Report ID",
                         "\nThe report is closed, no further action is needed."),
    "EMAIL_BOUNCED": ("EMAIL DELIVERY FAILED", "Report ID",
                      "\nCheck the mail log and resend once the cause is fixed."),
}


def _message_parts(title, hunter, action, detail=""):
    header, label, suffix = _MESSAGES[action]
    body = label + " = *" + title + "*\nReporter = *" + hunter + "*"
    if detail:
        body += "\nError = " + detail
    return header, body + suffix


def notify_slack(title, hunter, action, detail=""):
    try:
        webhook = Webhook.objects.get(webhook_service="SLACK").webhook_handle # SLACK WEBHOOK
        header, body = _message_parts(title, hunter, action, detail)
        payload = {
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": "\n*:warning: " + header + " :warning:*"}},
                {"type": "divider"},
                {"type": "section", "text": {"type": "mrkdwn", "text": body}},
            ]
        }

        logging.getLogger("Gerologger").debug(f"Sending Slack notification: {action} - {title}")
        response = requests.post(webhook, json.dumps(payload), timeout=10)
        response.raise_for_status()
        logging.getLogger("Gerologger").debug("Slack notification sent successfully")
        return True

    except requests.exceptions.Timeout:
        logging.getLogger("Gerologger").error(f"Slack webhook timeout (10s): {action} - {title}")
        return False
    except requests.exceptions.RequestException as e:
        logging.getLogger("Gerologger").error(f"Slack webhook failed: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        logging.getLogger("Gerologger").error(f"Slack notification error: {type(e).__name__}: {e}")
        return False


def notify_telegram(title, hunter, action, detail=""):
    try:
        # webhook = "https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}"
        webhook = Webhook.objects.get(webhook_service="TELEGRAM").webhook_handle # TELEGRAM WEBHOOK
        header, body = _message_parts(title, hunter, action, detail)
        message = "*\U0001F6A8 " + header + " \U0001F6A8*\n=========================\n" + body

        logging.getLogger("Gerologger").debug(f"Sending Telegram notification: {action} - {title}")
        response = requests.get(webhook+"&parse_mode=Markdown&text="+quote(message, safe=''), timeout=10)
        if response.status_code == 400:
            # MARKDOWN PARSE ERROR (STRAY _ OR * IN A TITLE OR SMTP ERROR) -- RESEND AS PLAIN TEXT
            response = requests.get(webhook+"&text="+quote(message, safe=''), timeout=10)
        response.raise_for_status()
        logging.getLogger("Gerologger").debug("Telegram notification sent successfully")
        return True

    except requests.exceptions.Timeout:
        logging.getLogger("Gerologger").error(f"Telegram webhook timeout (10s): {action} - {title}")
        return False
    except requests.exceptions.RequestException as e:
        logging.getLogger("Gerologger").error(f"Telegram webhook failed: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        logging.getLogger("Gerologger").error(f"Telegram notification error: {type(e).__name__}: {e}")
        return False


def notify(title, hunter, action, detail=""):
    results = []

    if Webhook.objects.filter(webhook_service="SLACK").exists():
        results.append(notify_slack(title, hunter, action, detail))

    if Webhook.objects.filter(webhook_service="TELEGRAM").exists():
        results.append(notify_telegram(title, hunter, action, detail))

    return any(results) if results else True
