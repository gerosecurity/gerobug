import requests
import json
from prerequisites.models import Webhook



def notify_slack(title, hunter):
    webhook = Webhook.objects.get(webhook_service="SLACK").webhook_handle # SLACK WEBHOOK
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

    return requests.post(webhook, json.dumps(payload))

def notify_telegram(title, hunter):
    webhook = Webhook.objects.get(webhook_service="TELEGRAM").webhook_handle # TELEGRAM WEBHOOK
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

    return requests.post(webhook, json.dumps(payload))

def notify(title, hunter):
    if Webhook.objects.filter(webhook_service="SLACK").exists():
        print("SLACK !")
        notify_slack(title, hunter)

    if Webhook.objects.filter(webhook_service="TELEGRAM").exists():
        notify_telegram(title, hunter)
