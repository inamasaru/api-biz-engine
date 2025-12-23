import os
from typing import Optional, Dict, Any


def log_notion(row: Dict[str, Any]) -> Optional[str]:
    token = os.getenv("NOTION_TOKEN", "").strip()
    db_id = os.getenv("NOTION_DB_ID", "").strip()
    if not (token and db_id):
        return None

    from notion_client import Client

    notion = Client(auth=token)

    props = {"Name": {"title": [{"text": {"content": row.get("name", "offer")}}]}}

    def num(v):
        try:
            return float(v)
        except Exception:
            return None

    if row.get("url"):
        props["URL"] = {"url": row["url"]}
    if num(row.get("final_score")) is not None:
        props["FinalScore"] = {"number": num(row["final_score"])}
    if num(row.get("gross_profit_yen")) is not None:
        props["GrossProfitYen"] = {"number": num(row["gross_profit_yen"])}
    if num(row.get("conv_prob")) is not None:
        props["ConvProb"] = {"number": num(row["conv_prob"])}

    page = notion.pages.create(parent={"database_id": db_id}, properties=props)
    return page.get("id")
