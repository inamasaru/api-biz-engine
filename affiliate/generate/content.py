import os
from typing import Dict
from openai import OpenAI

from affiliate.core.schema import Offer, Score

SYSTEM = """あなたは日本語のアフィリエイト記事編集者です。
誇張しない。医療/金融などは断定しない。事実不明は推測しない。
短く、読みやすく、見出しと箇条書きを多用する。"""


def _fallback_post(offer: Offer, score: Score) -> Dict[str, str]:
    title = f"{offer.title}｜今おすすめの理由"
    content = f"""## 結論
今は「期待利益 {score.final_score:.0f}」相当で狙い目です。

## ポイント
- 期待粗利（推定）: ¥{score.gross_profit_yen:.0f}
- 成約見込み（推定）: {score.conv_prob*100:.0f}%
- 情報源: {offer.source}

## 公式リンク
{offer.url}
"""
    return {"title": title, "content": content}


def generate_post(offer: Offer, score: Score) -> Dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _fallback_post(offer, score)

    model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    client = OpenAI(api_key=api_key)

    user = f"""
案件情報:
- タイトル: {offer.title}
- URL: {offer.url}
- 価格: {offer.price_yen}
- 固定報酬: {offer.payout_yen}
- 料率: {offer.commission_rate}
- 期待粗利: {score.gross_profit_yen:.0f}
- 成約見込み: {score.conv_prob:.2f}
- メタ: {offer.meta}

出力:
- content: Markdown
構成:
1) 結論（2行）
2) 根拠（箇条書き5つ）
3) こんな人におすすめ（箇条書き）
4) 注意点（断定しない）
5) CTA（リンク1回だけ）
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        text = resp.choices[0].message.content or ""
        title = f"{offer.title}｜おすすめ理由まとめ"
        return {"title": title[:32], "content": text}
    except Exception:
        return _fallback_post(offer, score)
