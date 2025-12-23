import os
from dataclasses import dataclass
from typing import Optional
import requests


@dataclass
class KeepaSignals:
    trend: float
    price_drop: float


KEEPA_PRODUCT_ENDPOINT = "https://api.keepa.com/product"


def _normalize_trend_from_csv_array(arr) -> float:
    if not arr or not isinstance(arr, list):
        return 0.5
    vals = [v for v in arr[-40:] if isinstance(v, (int, float)) and v >= 0]
    if len(vals) < 5:
        return 0.5
    diffs = [abs(vals[i] - vals[i - 1]) for i in range(1, len(vals))]
    avg_diff = sum(diffs) / max(len(diffs), 1)
    if avg_diff <= 50:
        return 0.85
    if avg_diff <= 150:
        return 0.7
    if avg_diff <= 400:
        return 0.55
    return 0.4


def query_keepa_signals_by_asin(asin: str, domain: int = 5) -> Optional[KeepaSignals]:
    key = os.getenv("KEEPA_API_KEY", "").strip()
    if not key:
        return None

    params = {
        "key": key,
        "domain": domain,
        "asin": asin,
        "history": 1,
        "stats": 1,
        "buybox": 1,
    }
    r = requests.get(KEEPA_PRODUCT_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    products = data.get("products") or []
    if not products:
        return None

    p = products[0]
    csv = p.get("csv") or []
    series = csv[0] if len(csv) > 0 else None
    trend = _normalize_trend_from_csv_array(series)

    stats = p.get("stats") or {}
    cur = stats.get("current") or {}
    avg = stats.get("avg") or {}
    price_drop = 0.5
    try:
        cur_bb = cur.get("BUY_BOX_SHIPPING") or cur.get("BUY_BOX") or None
        avg_bb = avg.get("BUY_BOX_SHIPPING") or avg.get("BUY_BOX") or None
        if cur_bb and avg_bb and avg_bb > 0:
            ratio = max(0.0, min(1.0, 1.0 - (cur_bb / avg_bb)))
            price_drop = max(0.1, min(0.95, ratio))
    except Exception:
        pass

    return KeepaSignals(trend=trend, price_drop=price_drop)
