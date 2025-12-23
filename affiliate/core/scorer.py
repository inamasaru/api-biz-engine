from typing import Optional, Dict, Any
from affiliate.core.schema import Offer, Score
from affiliate.core.utils import clamp


def estimate_gross_profit_yen(offer: Offer) -> float:
    if offer.payout_yen and offer.payout_yen > 0:
        return float(offer.payout_yen)
    if offer.price_yen and offer.commission_rate:
        return float(offer.price_yen) * float(offer.commission_rate)
    return 50.0


def score_offer(
    offer: Offer,
    keepa: Optional[Dict[str, Any]] = None,
) -> Score:
    gross = estimate_gross_profit_yen(offer)

    trend = 0.55
    price_drop = 0.50
    review_q = 0.50
    review_v = 0.50

    if keepa:
        trend = float(keepa.get("trend", trend))
        price_drop = float(keepa.get("price_drop", price_drop))

    rc = offer.meta.get("reviewCount")
    ra = offer.meta.get("reviewAverage")
    try:
        if rc is not None:
            review_v = clamp(float(rc) / 200.0, 0.15, 0.95)
        if ra is not None:
            review_q = clamp((float(ra) - 3.0) / 2.0, 0.10, 0.95)
    except Exception:
        pass

    conv = (
        0.35 * trend +
        0.25 * price_drop +
        0.20 * review_q +
        0.20 * review_v
    )
    conv = clamp(conv, 0.08, 0.90)

    final = gross * conv
    return Score(
        gross_profit_yen=gross,
        conv_prob=conv,
        final_score=final,
        reason={
            "trend": trend,
            "price_drop": price_drop,
            "review_q": review_q,
            "review_v": review_v,
        },
    )
