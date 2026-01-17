#!/usr/bin/env python3
import argparse
import csv
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: (r.get(k, "") or "").strip() for k in fieldnames})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=int(os.getenv("OUTREACH_BATCH", "25")))
    args = ap.parse_args()

    leads_path = Path("data/leads.csv")
    log_path = Path("data/outreach_log.csv")
    dnc_path = Path("data/dnc.csv")
    out_path = Path("reports/outreach_targets.csv")
    msg_path = Path("reports/outreach_message.txt")

    leads = read_csv(leads_path)
    sent = read_csv(log_path)
    dnc = read_csv(dnc_path)

    sent_set = set((r.get("contact_url","") or "").strip() for r in sent if (r.get("contact_url","") or "").strip())
    dnc_set  = set((r.get("contact_url","") or "").strip() for r in dnc  if (r.get("contact_url","") or "").strip())

    targets = []
    for r in leads:
        cu = (r.get("contact_url","") or "").strip()
        if not cu:
            continue
        if cu in sent_set:
            continue
        if cu in dnc_set:
            continue
        targets.append(r)
        if len(targets) >= args.batch_size:
            break

    write_csv(
        out_path,
        targets,
        fieldnames=["clinic_name","website_url","prefecture","contact_url","source_url"]
    )

    public_lp = os.getenv("PUBLIC_LP_URL", "https://inamasaru.github.io/api-biz-engine/")
    sender_name = os.getenv("SENDER_NAME", "稲村 優")
    sender_contact = os.getenv("SENDER_CONTACT", public_lp)  # メールが無い場合でも成立させる
    optout_url = os.getenv("OPTOUT_URL", public_lp.rstrip("/") + "/optout.html")

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    msg = f"""# Outreach message (generated {now})

件名：自由診療クリニックの集客導線 簡易監査のご案内（営業）

（本文テンプレ）
---
{{clinic_name}} ご担当者様

突然のご連絡失礼いたします。{sender_name}（連絡先：{sender_contact}）です。
自由診療クリニック向けに、広告・LP・予約導線の「改善運用」を提供しています（成果保証はしません）。

いま、同業種向けに
・現状導線の論点整理
・改善の優先順位（簡易版）
をまとめた「簡易監査レポート」を無償でお渡ししています（営業目的を含みます）。

ご希望の場合は、こちらからお申し込みください（所要2分）：
{public_lp}

今後のご連絡が不要な場合は、以下より停止できます：
{optout_url}
---
"""
    msg_path.parent.mkdir(parents=True, exist_ok=True)
    msg_path.write_text(msg, encoding="utf-8")

    print(f"[OK] targets={len(targets)} -> {out_path}")
    print(f"[OK] message -> {msg_path}")

if __name__ == "__main__":
    main()
