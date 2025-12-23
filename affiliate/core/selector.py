import os
from typing import List, Tuple

from affiliate.adapters.a8_feed import load_a8_offers
from affiliate.adapters.rakuten_client import search_rakuten_items
from affiliate.adapters.keepa_client import query_keepa_signals_by_asin
from affiliate.core.schema import Offer, Score
from affiliate.core.scorer import score_offer


def collect_offers() -> List[Offer]:
    offers: List[Offer] = []

    offers.extend(load_a8_offers())

    keywords = os.getenv("RAKUTEN_KEYWORDS", "").strip()
    if keywords:
        for kw in [k.strip() for k in keywords.split(",") if k.strip()]:
            offers.extend(search_rakuten_items(kw, hits=10))

    return offers


def pick_topN(top_n: int = 3) -> List[Tuple[Offer, Score]]:
    offers = collect_offers()

    ranked: List[Tuple[Offer, Score]] = []
    for off in offers:
        keepa_sig = None
        asin = off.meta.get("asin")
        if asin:
            ks = query_keepa_signals_by_asin(str(asin))
            if ks:
                keepa_sig = {"trend": ks.trend, "price_drop": ks.price_drop}

        sc = score_offer(off, keepa=keepa_sig)
        ranked.append((off, sc))

    ranked.sort(key=lambda x: x[1].final_score, reverse=True)
    filtered = [(o, s) for (o, s) in ranked if s.final_score >= 80.0]
    return (filtered or ranked)[: max(1, top_n)]
