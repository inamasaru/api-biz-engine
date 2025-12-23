from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Source(str, Enum):
    A8 = "A8"
    RAKUTEN = "RAKUTEN"
    AMAZON = "AMAZON"


@dataclass
class Offer:
    source: Source
    title: str
    url: str
    price_yen: Optional[float] = None
    payout_yen: Optional[float] = None
    commission_rate: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Score:
    gross_profit_yen: float
    conv_prob: float
    final_score: float
    reason: Dict[str, Any] = field(default_factory=dict)
