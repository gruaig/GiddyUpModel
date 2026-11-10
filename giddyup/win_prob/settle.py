#!/usr/bin/env python3
"""Settle logged predictions against actual results.

Reads predictions_log.csv, looks up each finished race's result (finishing
position + BSP) in horse_db, and reports how the TAKE PRICE / LAY picks actually
did — hit-rate and ROI at BSP.

Usage:
    .venv/bin/python win_prob/settle.py            # settle all logged dates
    .venv/bin/python win_prob/settle.py --date 2026-11-10
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "predictions_log.csv"
DSN = "postgresql://postgres:password@localhost:5433/horse_db"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="only settle this race_date (YYYY-MM-DD)")
    args = ap.parse_args()

    if not LOG_PATH.exists():
        raise SystemExit("No predictions_log.csv yet.")

    rows = list(csv.DictReader(LOG_PATH.open()))
    if args.date:
        rows = [r for r in rows if r["race_date"] == args.date]
    if not rows:
        raise SystemExit("No logged predictions to settle.")

    dates = sorted({r["race_date"] for r in rows})
    print(f"Settling {len(rows)} predictions across {len(dates)} date(s): {dates}")

    with psycopg.connect(DSN) as conn:
        results = {}  # (date, course_norm, off_hm, horse_norm) -> (pos_num, bsp)
        for d in dates:
            cur = conn.execute(
                """
                SELECT r.race_date::text, c.course_name, r.off_time::text, h.horse_name, ru.pos_num, ru.win_bsp
                FROM racing.runners ru
                JOIN racing.races r ON r.race_id = ru.race_id
                JOIN racing.courses c ON c.course_id = r.course_id
                JOIN racing.horses h ON h.horse_id = ru.horse_id
                WHERE r.race_date = %s::date
                """, (d,))
            for rd, course, off, horse, pos, bsp in cur.fetchall():
                off_hm = (off or "")[:5]
                results[(rd, norm(course), off_hm, norm(horse))] = (pos, bsp)

    settled = []
    for r in rows:
        key = (r["race_date"], norm(r["course"]), (r["off_time"] or "")[:5], norm(r["horse"]))
        pos, bsp = results.get(key, (None, None))
        r = dict(r)
        r["pos_num"] = "" if pos is None else str(pos)
        r["bsp"] = "" if bsp is None else f"{bsp:.2f}"
        r["won"] = "1" if pos == 1 else ("0" if pos is not None else "")
        settled.append(r)

    # summary by bet type (using the action column from the log)
    def report(action, won_value):
        picks = [r for r in settled if r["action"] == action and r["won"] != ""]
        if not picks:
            return
        n = len(picks)
        wins = sum(1 for r in picks if r["won"] == "1")
        bsp_vals = [float(r["bsp"]) for r in picks if r["bsp"]]
        # back ROI at BSP (flat 1-unit): win -> bsp-1, lose -> -1
        roi = sum((float(r["bsp"]) - 1 if r["won"] == "1" else -1.0) for r in picks if r["bsp"]) / n * 100
        hit = wins / n * 100
        print(f"  {action:11s}: {n:3d} settled, {'won' if won_value == '1' else 'lost'} {hit:5.1f}%, ROI@BSP {roi:+6.1f}%")
        return roi

    print("\n=== Performance by action ===")
    report("TAKE PRICE", "1")
    report("LAY", "0")

    # write settled log
    out = ROOT / "predictions_settled.csv"
    fields = ["logged_at", "race_date", "course", "off_time", "race_id", "horse",
              "win_pct", "fair", "bf_back", "bf_lay", "ev_bf_pct", "action", "pos_num", "bsp", "won"]
    new = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for r in settled:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"\nWrote {len(settled)} settled rows to {out}")


if __name__ == "__main__":
    main()
