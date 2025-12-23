import os
import requests


def notify_slack(text: str) -> bool:
    url = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        return False
    try:
        r = requests.post(url, json={"text": text[:39000]}, timeout=15)
        return r.status_code in (200, 201)
    except Exception:
        return False
