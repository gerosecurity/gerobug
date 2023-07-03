import requests
import json
from prerequisites.models import Webhook



def notify_slack(title, hunter, action):
    webhook = Webhook.objects.get(webhook_service="SLACK").webhook_handle # SLACK WEBHOOK
    if action == "NEW_REPORT":
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n*:warning: NEW REPORT RECEIVED :warning:*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Title = *"+title+"*\nReporter = *"+hunter+"*"
                    }
                }
            ]
        }
    elif action == "NEW_UPDATE":
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n*:warning: NEW UPDATE/AMEND RECEIVED :warning:*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Report ID = *"+title+"*\nReporter = *"+hunter+"*"
                    }
                }
            ]
        }
    elif action == "NEW_APPEAL":
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n*:warning: NEW APPEAL RECEIVED :warning:*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Report ID = *"+title+"*\nReporter = *"+hunter+"*"
                    }
                }
            ]
        }
    elif action == "NEW_AGREE":
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n*:warning: HUNTER AGREEMENT RECEIVED :warning:*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Report ID = *"+title+"*\nReporter = *"+hunter+"*\nReport will be automatically moved to the next phase."
                    }
                }
            ]
        }
    elif action == "NEW_NDA":
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n*:warning: NEW NDA SUBMISSION RECEIVED :warning:*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Report ID = *"+title+"*\nReporter = *"+hunter+"*"
                    }
                }
            ]
        }

    return requests.post(webhook, json.dumps(payload))

def notify_telegram(title, hunter, action):
    # webhook = "https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}"
    webhook = Webhook.objects.get(webhook_service="TELEGRAM").webhook_handle # TELEGRAM WEBHOOK
    if action == "NEW_REPORT":
        message = "\n\
        *🚨 NEW REPORT RECEIVED 🚨*\n\
        =========================\n\
        Title       = *"+title+"*\n\
        Reporter    = *"+hunter+"*"
    elif action == "NEW_UPDATE":
        message = "\n\
        *🚨 NEW UPDATE/AMEND RECEIVED 🚨*\n\
        =========================\n\
        Report ID   = *"+title+"*\n\
        Reporter    = *"+hunter+"*"
    elif action == "NEW_APPEAL":
        message = "\n\
        *🚨 NEW APPEAL RECEIVED 🚨*\n\
        =========================\n\
        Report ID   = *"+title+"*\n\
        Reporter    = *"+hunter+"*"
    elif action == "NEW_AGREE":
        message = "\n\
        *🚨 HUNTER AGREEMENT RECEIVED 🚨*\n\
        =========================\n\
        Report ID   = *"+title+"*\n\
        Reporter    = *"+hunter+"*\n\
        Report will be automatically moved to the next phase."
    elif action == "NEW_NDA":
        message = "\n\
        *🚨 NEW NDA SUBMISSION RECEIVED 🚨*\n\
        =========================\n\
        Report ID   = *"+title+"*\n\
        Reporter    = *"+hunter+"*"

    webhook = webhook+"&parse_mode=Markdown&text="+message
    return requests.get(webhook)

def notify(title, hunter, action):
    if Webhook.objects.filter(webhook_service="SLACK").exists():
        notify_slack(title, hunter, action)

    if Webhook.objects.filter(webhook_service="TELEGRAM").exists():
        notify_telegram(title, hunter, action)
