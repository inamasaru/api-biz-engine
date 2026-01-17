import json, os, random, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))

PRICE_YEN = int(os.getenv("PRICE_YEN", "2000000"))
# 仮メトリクス（最初はダミーでOK。後で実データに差し替える）
def calc_metrics():
    # 返信率/面談化率/成立率のダミー（最初は一定で出してOK）
    reply = float(os.getenv("REPLY_RATE", "0.02"))
    meeting = float(os.getenv("MEETING_RATE", "0.005"))
    close = float(os.getenv("CLOSE_RATE", "0.10"))
    # cpaは仮：広告費 / 予約数（ここでは予約数= 面談数×0.6仮）
    spend = int(os.getenv("SPEND_YEN", "300000"))
    bookings = max(1, int(1000 * meeting * 0.6))
    cpa = spend / bookings
    return {
        "reply_rate": reply,
        "meeting_rate": meeting,
        "close_rate": close,
        "spend_yen": spend,
        "bookings_est": bookings,
        "cpa_yen": round(cpa, 2),
        "price_yen": PRICE_YEN
    }

def decide(metrics):
    cpa = metrics["cpa_yen"]
    price = metrics["price_yen"]
    go = (cpa <= price * 0.30) and (metrics["reply_rate"] >= 0.02) and (metrics["meeting_rate"] >= 0.005)
    stop = (cpa >= price * 0.50) or (metrics["reply_rate"] < 0.01 and float(os.getenv("DAYS_LOW_REPLY","0")) >= 7)
    if stop:
        return {"go": False, "reason": "STOP条件に抜抓", "metrics": metrics}
    return {"go": bool(go), "reason": "GO条件を満たす" if go else "改善続行（GO未段）", "metrics": metrics}

def write_latest(decision):
    Path("docs").mkdir(parents=True, exist_ok=True)
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    m = decision["metrics"]
    lines = [
        f"# Daily Report ({now})",
        "",
        f"- decision: {'GO' if decision['go'] else 'STOP/IMPROVE'}",
        f"- reason: {decision['reason']}",
        "",
        "## Metrics",
        f"- reply_rate: {m['reply_rate']:.4f}",
        f"- meeting_rate: {m['meeting_rate']:.4f}",
        f"- close_rate: {m['close_rate']:.4f}",
        f"- spend_yen: {m['spend_yen']}",
        f"- bookings_est: {m['bookings_est']}",
        f"- cpa_yen: {m['cpa_yen']}",
        f"- price_yen: {m['price_yen']}",
        "",
        "## Next (auto)",
        "- テンプレ改善案を生成し、LPの見出し/CTA文言を微調整（※賞大表現フィルタ適用）",
    ]
    Path("docs/latest.md").write_text("\n".join(lines), encoding="utf-8")

def main():
    metrics = calc_metrics()
    decision = decide(metrics)
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    write_latest(decision)

if __name__ == "__main__":
    main()
