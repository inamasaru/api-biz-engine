import os
import requests


def main():
    token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")
    notion_version = os.environ.get("NOTION_VERSION", "2025-09-03")
    if not token or not database_id:
        raise SystemExit("NOTION_TOKEN and NOTION_DATABASE_ID must be set")
    url = f"https://api.notion.com/v1/databases/{database_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": notion_version,
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    data_sources = data.get("data_sources", [])
    if not data_sources:
        print("No data sources found")
        return
    first_ds = data_sources[0]
    if isinstance(first_ds, dict):
        print(first_ds.get("id"))
    else:
        print(first_ds)


if __name__ == "__main__":
    main()
