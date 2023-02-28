import requests
import json


def notify_slack(title, hunter):
    webhook = "https://hooks.slack.com/services/xxx/xxx/xxx" # SLACK WEBHOOK
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
