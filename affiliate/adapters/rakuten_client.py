import os
from typing import List
import requests

from affiliate.core.schema import Offer, Source

RAKUTEN_ENDPOINT = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"


def search_rakuten_items(keyword: str, hits: int = 10) -> List[Offer]:
    app_id = os.getenv("RAKUTEN_APP_ID", "").strip()
    if not app_id:
        return []

    affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID", "").strip() or None
    default_rate = float(os.getenv("RAKUTEN_COMMISSION_RATE_DEFAULT", "0.01") or "0.01")

    params = {
        "applicationId": app_id,
        "keyword": keyword,
        "hits": min(max(hits, 1), 30),
        "page": 1,
        "format": "json",
    }
    if affiliate_id:
        params["affiliateId"] = affiliate_id

    r = requests.get(RAKUTEN_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    items = data.get("Items", [])
    offers: List[Offer] = []
    for it in items:
        item = it.get("Item", {})
        title = item.get("itemName")
        url = item.get("affiliateUrl") or item.get("itemUrl")
        price = item.get("itemPrice")
        img = None
        imgs = item.get("mediumImageUrls") or []
        if imgs and isinstance(imgs, list):
            img = (imgs[0].get("imageUrl") or "").replace("?_ex=128x128", "")

        if not title or not url or not price:
            continue

        offers.append(
            Offer(
                source=Source.RAKUTEN,
                title=str(title),
                url=str(url),
                price_yen=float(price),
                payout_yen=None,
                commission_rate=float(default_rate),
                category=None,
                image_url=img,
                meta={
                    "keyword": keyword,
                    "shopName": item.get("shopName"),
                    "reviewCount": item.get("reviewCount"),
                    "reviewAverage": item.get("reviewAverage"),
                },
            )
        )
    return offers
