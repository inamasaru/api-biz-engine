import csv
import io
import os
from typing import List, Optional
import requests

from affiliate.core.schema import Offer, Source


def _read_csv_text() -> Optional[str]:
    url = os.getenv("A8_FEED_CSV_URL", "").strip()
    path = os.getenv("A8_FEED_CSV_PATH", "").strip()

    if url:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.text

    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return None


def load_a8_offers() -> List[Offer]:
    """
    A8案件は最小構成として CSV フィード投入で運用する。
    CSV列（最低限）: title,url,payout_yen
    任意: price_yen,commission_rate,category,notes
    """
    text = _read_csv_text()
    if not text:
        return []

    reader = csv.DictReader(io.StringIO(text))
    offers: List[Offer] = []
    for row in reader:
        title = (row.get("title") or "").strip()
        url = (row.get("url") or "").strip()
        if not title or not url:
            continue

        payout_yen = float((row.get("payout_yen") or "0").strip() or 0)
        price_yen = float((row.get("price_yen") or "0").strip() or 0)
        commission_rate = float((row.get("commission_rate") or "0").strip() or 0)
        category = (row.get("category") or "").strip() or None
        notes = (row.get("notes") or "").strip() or None

        offers.append(
            Offer(
                source=Source.A8,
                title=title,
                url=url,
                price_yen=price_yen if price_yen > 0 else None,
                payout_yen=payout_yen if payout_yen > 0 else None,
                commission_rate=commission_rate if commission_rate > 0 else None,
                category=category,
                image_url=None,
                meta={"notes": notes} if notes else {},
            )
        )
    return offers
