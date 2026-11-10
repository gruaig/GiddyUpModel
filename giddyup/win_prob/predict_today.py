#!/usr/bin/env python3
"""Predict today's (or a given date's) races: win probability, fair odds, BSP estimate.

Fetches Sporting Life racecards + race details + bookmaker decimal odds, joins each
runner to its historical form in horse_db, computes the SAME leak-free features as
win_prob_model.py, and scores them with the trained LightGBM model.

Output per race: runner, jockey, opening price, model win %, fair odds, and the
value edge vs the opening bookmaker price.

Usage:
    python predict_today.py                 # today
    python predict_today.py --date 2026-11-11
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import polars as pl
import lightgbm as lgb

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import win_prob_model as M  # FEATURES, compute_features, categorical maps

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36", "Accept": "application/json"}
SL = "https://www.sportinglife.com/api/horse-racing"


def fetch_json(url, retries=4):
    req = urllib.request.Request(url, headers=UA)
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in {500, 502, 503} or attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise last


COUNTRY_SUFFIX = re.compile(
    r"\s*\((IRE|GB|FR|USA|US|GER|AUS|NZ|SAF|ITY|SPA|JPN|ARG|BRZ|CHI|URU|POL|CZE|DEN|NOR|SWE|BEL|NED|SUI|AUT|HUN|SVK|TUR|UAE|KSA|QAT)\)\s*",
    re.IGNORECASE,
)


def norm(s):
    # strip Betfair country-code suffixes, fold diacritics (é -> e), drop non-alphanumeric
    s = COUNTRY_SUFFIX.sub("", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def derive_race_type(name, distance):
    s = f"{name or ''} {distance or ''}".lower()
    if "chase" in s or "steeple" in s:
        return "Chase"
    if "hurdle" in s:
        return "Hurdle"
    if "nh flat" in s or "bumper" in s or "i.n.h. flat" in s:
        return "NH Flat"
    return "Flat"


def dist_to_furlongs(distance):
    if not distance:
        return None
    total = 0.0
    for v, u in re.findall(r"(\d+(?:\.\d+)?)([mfy])", distance.lower().replace(" ", "").replace(",", "")):
        v = float(v)
        total += v * (8 if u == "m" else 1 if u == "f" else 1 / 220)
    return total or None


def lbs_from_handicap(h):
    if not h or "-" not in str(h):
        return None
    st, lb = str(h).split("-", 1)
    try:
        return int(st) * 14 + int(lb)
    except ValueError:
        return None


def surface_code(surf):
    if isinstance(surf, dict):
        surf = surf.get("surface") or surf.get("name") or ""
    s = (surf or "").lower()
    if s in {"aw", "all-weather", "all weather", "fibresand", "polytrack", "tapeta"}:
        return "AW"
    return "Turf"


def get_betting(race_id):
    """Return {cloth_number: best decimal odds} for a race."""
    d = fetch_json(f"{SL}/v2/racing/betting/{race_id}")
    out = {}
    for r in d.get("rides", []):
        cloth = r.get("cloth_number")
        best = None
        for bo in r.get("bookmakerOdds", []):
            if bo.get("decimalOdds"):
                best = bo["decimalOdds"] if best is None else min(best, bo["decimalOdds"])
        if best and cloth:
            out[int(cloth)] = float(best)
    return out


def build_today(date_str, maps):
    cards = fetch_json(f"{SL}/racing/racecards/{date_str}")
    gb_ire = {"ENG", "SCO", "Scot", "Wale", "Eire", "IRE", "UK"}
    rows = []
    for m in cards:
        ms = m.get("meeting_summary", {}) or {}
        course_obj = ms.get("course") or {}
        course = course_obj.get("name")
        country_short = (course_obj.get("country") or {}).get("short_name") or ""
        if country_short not in gb_ire:
            continue  # skip non-GB/IRE meetings (FR, USA, ...)
        region = "IRE" if country_short in {"Eire", "IRE"} else "GB"
        for rc in m.get("races", []):
            rid = (rc.get("race_summary_reference") or {}).get("id")
            if not rid:
                continue
            d = fetch_json(f"{SL}/race/{rid}")
            rs, rides = d.get("race_summary", {}) or {}, d.get("rides", [])
            odds = get_betting(rid)
            rt = derive_race_type(rs.get("name") or rc.get("name"), rc.get("distance"))
            dist_f = dist_to_furlongs(rc.get("distance"))
            surf = surface_code(rc.get("course_surface") or rs.get("surface"))
            for r in rides:
                h = r.get("horse", {}) or {}
                name = h.get("name")
                if not name:
                    continue
                cloth = r.get("cloth_number")
                hid = maps["horse"].get(norm(name), -(10_000_000 + hash(norm(name)) % 5_000_000))
                tid = maps["trainer"].get(norm((r.get("trainer") or {}).get("name")), 0)
                jid = maps["jockey"].get(norm((r.get("jockey") or {}).get("name")), 0)
                cid = maps["course"].get(norm(course), 0)
                rows.append({
                    "runner_id": 0,
                    "race_id": int(rid),
                    "race_date": date_str,
                    "region": region,
                    "course_id": cid,
                    "course_name": course,
                    "off_time": rc.get("time"),
                    "race_type": rt,
                    "class": rc.get("race_class") or "",
                    "dist_f": dist_f,
                    "dist_m": int(dist_f * 201.168) if dist_f else None,
                    "going": rc.get("going"),
                    "surface": surf,
                    "ran": len(rides),
                    "horse_id": hid,
                    "trainer_id": tid,
                    "jockey_id": jid,
                    "num": cloth,
                    "draw": r.get("draw_number"),
                    "age": h.get("age"),
                    "sex": (h.get("sex") or {}).get("type") or "",
                    "lbs": lbs_from_handicap(r.get("handicap")),
                    "hg": None,
                    "official_rating": r.get("official_rating"),
                    "win_morningwap": odds.get(cloth),
                    "pos_num": None,
                    "beaten_lengths": None,
                    "rpr": None,
                    "won": 0,
                    "name": name,
                    "jockey_name": (r.get("jockey") or {}).get("name"),
                    "trainer_name": (r.get("trainer") or {}).get("name"),
                })
    schema = {
        "runner_id": pl.Int64, "race_id": pl.Int64, "course_id": pl.Int64,
        "horse_id": pl.Int64, "trainer_id": pl.Int64, "jockey_id": pl.Int64,
        "num": pl.Int64, "draw": pl.Int64, "age": pl.Int64, "lbs": pl.Int64,
        "official_rating": pl.Int64, "dist_f": pl.Float64, "dist_m": pl.Int64,
        "ran": pl.Int64, "win_morningwap": pl.Float64, "pos_num": pl.Int64,
        "beaten_lengths": pl.Float64, "rpr": pl.Int64, "won": pl.Int64,
        "race_date": pl.Utf8, "region": pl.Utf8, "off_time": pl.Utf8,
        "race_type": pl.Utf8, "class": pl.Utf8, "going": pl.Utf8, "surface": pl.Utf8,
        "sex": pl.Utf8, "hg": pl.Utf8, "name": pl.Utf8, "jockey_name": pl.Utf8,
        "trainer_name": pl.Utf8, "course_name": pl.Utf8,
    }
    return pl.DataFrame(rows, schema_overrides=schema)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=str(dt.date.today()))
    ap.add_argument("--race", default=None, help="only show this race id")
    ap.add_argument("--url", default=None, help="SL racecard URL (extracts date + race id)")
    ap.add_argument("--max-fair", type=float, default=20.0, help="drop long-shots with fair odds above this (default 20)")
    ap.add_argument("--margin", type=float, default=0.05, help="min edge for an action (default 0.05 = 5%)")
    ap.add_argument("--bank", type=float, default=1000.0, help="bankroll balance for stake sizing (default 1000)")
    ap.add_argument("--stake-pct", type=float, default=1.0, help="flat stake as % of bankroll (default 1%)")
    ap.add_argument("--drift-max", type=float, default=0.10, help="skip BACK bets predicted to drift more than this (log BSP/open; default 0.10)")
    ap.add_argument("--max-per-race", type=int, default=1, help="mark only the top N bets per race (default 1)")
    ap.add_argument("--model", default=str(ROOT / "win_prob_model.txt"))
    args = ap.parse_args()

    if args.url:
        m = re.search(r"/(\d{4}-\d{2}-\d{2})/", args.url)
        rm = re.search(r"/racecard/(\d+)", args.url)
        if not m or not rm:
            raise SystemExit("Could not parse date/race from URL (expect .../racecards/YYYY-MM-DD/.../racecard/<id>/...)")
        args.date = m.group(1)
        args.race = rm.group(1)
        print(f"URL -> date {args.date}, race {args.race}")

    date_str = args.date

    conn_str = M.get_connection_string()
    import psycopg
    with psycopg.connect(conn_str) as conn:
        maps = {
            "horse": {norm(n): hid for hid, n in conn.execute("SELECT horse_id, horse_name FROM racing.horses").fetchall()},
            "trainer": {norm(n): tid for tid, n in conn.execute("SELECT trainer_id, trainer_name FROM racing.trainers").fetchall()},
            "jockey": {norm(n): jid for jid, n in conn.execute("SELECT jockey_id, jockey_name FROM racing.jockeys").fetchall()},
            "course": {norm(n): cid for cid, n in conn.execute("SELECT course_id, course_name FROM racing.courses").fetchall()},
        }

    print(f"Fetching {date_str} card ...")
    today = build_today(date_str, maps)
    print(f"  {len(today):,} runners across {today['race_id'].n_unique()} races")

    # ---- historical form (all past races) ----
    q = """
    SELECT ru.runner_id, ru.race_id, r.race_date, r.region, r.course_id, r.off_time,
           r.race_type, r.class, r.dist_f, r.dist_m, r.going, r.surface, r.ran,
           ru.horse_id, ru.trainer_id, ru.jockey_id, ru.num, ru.draw, ru.age, ru.sex,
           ru.lbs, ru.hg, ru.or AS official_rating, ru.win_morningwap, ru.pos_num,
           ru.btn AS beaten_lengths, ru.rpr, ru.win_flag AS won
    FROM racing.runners ru JOIN racing.races r ON r.race_id = ru.race_id
    WHERE r.race_date < DATE '{d}' AND ru.horse_id IS NOT NULL
    """.format(d=date_str)
    print("Loading historical form ...")
    hist = pl.read_database_uri(query=q, uri=conn_str)
    print(f"  {len(hist):,} historical rows")

    # add output-only columns to hist so schemas match
    hist = hist.with_columns([
        pl.lit(None, dtype=pl.Utf8).alias("name"),
        pl.lit(None, dtype=pl.Utf8).alias("jockey_name"),
        pl.lit(None, dtype=pl.Utf8).alias("trainer_name"),
        pl.lit(None, dtype=pl.Utf8).alias("course_name"),
    ])

    # align: keep a canonical column order
    cols = ["runner_id", "race_id", "race_date", "region", "course_id", "off_time",
            "race_type", "class", "dist_f", "dist_m", "going", "surface", "ran",
            "horse_id", "trainer_id", "jockey_id", "num", "draw", "age", "sex",
            "lbs", "hg", "official_rating", "win_morningwap", "pos_num",
            "beaten_lengths", "rpr", "won", "name", "jockey_name", "trainer_name", "course_name"]
    today = today.select(cols)
    hist = hist.select(cols)
    # canonical dtypes so the vertical concat is type-safe
    dtypes = {
        "runner_id": pl.Int64, "race_id": pl.Int64, "race_date": pl.Date,
        "course_id": pl.Int64, "off_time": pl.Utf8, "dist_f": pl.Float64,
        "dist_m": pl.Int64, "ran": pl.Int64, "horse_id": pl.Int64,
        "trainer_id": pl.Int64, "jockey_id": pl.Int64, "num": pl.Int64,
        "draw": pl.Int64, "age": pl.Int64, "lbs": pl.Int64,
        "official_rating": pl.Int64, "win_morningwap": pl.Float64,
        "pos_num": pl.Int64, "beaten_lengths": pl.Float64, "rpr": pl.Int64,
        "won": pl.Int32, "hg": pl.Utf8,
    }
    today = today.with_columns([pl.col(k).cast(v) for k, v in dtypes.items() if k in today.columns])
    hist = hist.with_columns([pl.col(k).cast(v) for k, v in dtypes.items() if k in hist.columns])

    full = pl.concat([hist, today], how="vertical").with_columns(
        pl.col("race_id").cast(pl.Utf8).alias("race_key"),
    )
    field = full.group_by("race_key").agg(pl.len().alias("field_size"))
    full = full.join(field, on="race_key")
    full = M.compute_features(full)

    # score today's runners only
    tod = full.filter(pl.col("race_date") == pl.lit(date_str).str.strptime(pl.Date, "%Y-%m-%d"))
    features = [f for f in M.FEATURES if f in tod.columns]
    model = lgb.Booster(model_file=args.model)
    p = model.predict(tod.select(features).to_numpy())

    # apply isotonic calibration (fixes favourite/longshot bias), then normalise per race
    try:
        import joblib
        iso = joblib.load(ROOT / "iso_calib.joblib")
        p = iso.predict(p)
        print("  Applied isotonic calibration.")
    except Exception as e:
        print(f"  No isotonic calibrator ({e}); using raw probabilities.")

    tod = tod.with_columns(pl.Series("prob_raw", p))
    # normalize per race so probabilities sum to ~1
    race_s = tod.group_by("race_id").agg(pl.col("prob_raw").sum().alias("_s"))
    tod = tod.join(race_s, on="race_id").with_columns(
        (pl.col("prob_raw") / pl.col("_s")).alias("prob")
    ).drop("_s", "prob_raw")
    tod = tod.with_columns([
        (1.0 / pl.col("prob")).clip(lower_bound=1.01).alias("fair_odds"),
        (pl.col("prob") * pl.col("win_morningwap") - 1.0).alias("edge"),
    ])

    # ---- Betfair exchange prices (live, ~2% margin) ----
    print("Fetching Betfair exchange prices ...")
    import betfair_client as bf
    bf_client = bf.login()
    bf_prices = bf.get_prices(bf_client, date_str)
    bf_client.logout()
    print(f"  {len(bf_prices)} Betfair win markets")

    race_bp = {}
    for rid in tod["race_id"].unique(maintain_order=True):
        r0 = tod.filter(pl.col("race_id") == rid)
        course, off = r0["course_name"][0], r0["off_time"][0]
        runners = bf.match_race(bf_prices, course, off)
        race_bp[rid] = {r["norm"]: (r["back"], r["lay"]) for r in runners} if runners else {}

    bf_rows = []
    for r in tod.iter_rows(named=True):
        b, l = race_bp.get(r["race_id"], {}).get(norm(r["name"]), (None, None))
        bf_rows.append((b, l))
    tod = tod.with_columns([
        pl.Series("bf_back", [b for b, l in bf_rows], dtype=pl.Float64),
        pl.Series("bf_lay", [l for b, l in bf_rows], dtype=pl.Float64),
    ]).with_columns(
        (pl.col("prob") * pl.col("bf_back") - 1.0).alias("edge_bf"),
        (1.0 - pl.col("prob") * pl.col("bf_lay")).alias("lay_edge"),
    )

    # ---- drift model (predict shorten_score = log BSP - log opening) ----
    try:
        drift_model = lgb.Booster(model_file=str(ROOT / "drift_model.txt"))
        tod = tod.with_columns(pl.Series("drift_score", drift_model.predict(tod.select(features).to_numpy())))
        print("  Applied drift model.")
    except Exception as e:
        tod = tod.with_columns(pl.lit(0.0, dtype=pl.Float64).alias("drift_score"))
        print(f"  No drift model ({e}); drift filter skipped.")

    # ---- place model (predict top-2/3/4 probability) + each-way terms ----
    try:
        place_model = lgb.Booster(model_file=str(ROOT / "place_model.txt"))
        tod = tod.with_columns(pl.Series("place_prob", place_model.predict(tod.select(features).to_numpy())))
        tod = tod.with_columns([
            pl.when(pl.col("field_size") <= 4).then(1.0)
            .when(pl.col("field_size") <= 7).then(2.0)
            .when(pl.col("field_size") <= 15).then(3.0)
            .otherwise(4.0).alias("n_places"),
            pl.when(pl.col("field_size") <= 7).then(0.25)
            .when(pl.col("field_size") <= 15).then(0.20)
            .otherwise(0.25).alias("place_frac"),
        ])
        tod = tod.with_columns([
            (1.0 + (pl.col("bf_back") - 1.0) * pl.col("place_frac")).alias("place_odds"),
            (pl.col("place_prob") * (1.0 + (pl.col("bf_back") - 1.0) * pl.col("place_frac")) - 1.0).alias("place_edge"),
            ((pl.col("prob") * pl.col("bf_back") - 1.0 + pl.col("place_prob") * (1.0 + (pl.col("bf_back") - 1.0) * pl.col("place_frac")) - 1.0) / 2.0).alias("ew_edge"),
        ])
        print("  Applied place model.")
    except Exception as e:
        tod = tod.with_columns([
            pl.lit(None, dtype=pl.Float64).alias("place_prob"),
            pl.lit(None, dtype=pl.Float64).alias("place_edge"),
            pl.lit(None, dtype=pl.Float64).alias("ew_edge"),
        ])
        print(f"  No place model ({e}); place bets skipped.")

    print("\n" + "=" * 96)
    print(f"PREDICTIONS — {date_str}   (model trained up to 2025, tested on 2026)")
    print("=" * 96)
    race_ids = tod["race_id"].unique(maintain_order=True)
    if args.race:
        race_ids = [r for r in race_ids if str(r) == str(args.race)]
        if not race_ids:
            raise SystemExit(f"Race {args.race} not found for {date_str} (GB/IRE cards)")

    # skip races that have already gone off, and sort the rest soonest-first
    now_dt = dt.datetime.now()
    kept = []  # (off_time, rid)
    for rid in race_ids:
        r0 = tod.filter(pl.col("race_id") == rid)
        otime = r0["off_time"][0] or ""
        if otime:
            try:
                race_dt = dt.datetime.strptime(f"{date_str} {otime}", "%Y-%m-%d %H:%M")
                if race_dt <= now_dt:
                    continue  # already gone off
            except Exception:
                pass
        kept.append((otime, rid))
    n_skipped = len(race_ids) - len(kept)
    if n_skipped:
        print(f"  (skipped {n_skipped} race(s) that have already gone off)")
    kept.sort(key=lambda x: x[0])  # soonest off-time first
    race_ids = [rid for _t, rid in kept]
    def _action(fair, bb, bl, drift):
        if fair is None or (bb is None and bl is None):
            return "NO BF"
        if bb and bb >= fair * (1 + args.margin):
            if drift is not None and drift > args.drift_max:
                return "DRIFTER"   # value but predicted to drift -> avoid back
            return "TAKE PRICE"    # back: exchange offers longer than fair
        if bl and bl <= fair * (1 - args.margin):
            return "LAY"           # lay: exchange offers shorter than fair
        return "LEAVE"

    flat_stake = args.bank * args.stake_pct / 100.0

    def _stake(act, lay):
        # flat-liability sizing: BACK uses the flat stake; LAY uses flat LIABILITY
        if act == "TAKE PRICE":
            return f"£{flat_stake:.0f}"
        if act == "LAY" and lay and lay > 1:
            backer = flat_stake / (lay - 1.0)
            return f"L£{flat_stake:.0f}(£{backer:.2f})"
        return "-"

    for rid in race_ids:
        sub = tod.filter(pl.col("race_id") == rid)
        course = sub["course_name"][0] or ""
        otime = sub["off_time"][0] or ""
        sub = sub.filter(pl.col("fair_odds") <= args.max_fair)
        if len(sub) == 0:
            continue
        # rank actionable bets by value, mark the top N per race
        actionable = []
        for row in sub.iter_rows(named=True):
            act = _action(row["fair_odds"], row["bf_back"], row["bf_lay"], row["drift_score"])
            if act == "TAKE PRICE":
                actionable.append((row["edge_bf"] or 0.0, row["name"]))
            elif act == "LAY":
                actionable.append((row["lay_edge"] or 0.0, row["name"]))
        actionable.sort(reverse=True)
        top_names = {name for _v, name in actionable[:args.max_per_race]}
        sub = sub.sort("edge_bf", descending=True, nulls_last=True)
        print(f"\n--- {course} {otime}  (race {rid}, {len(sub)} runners) ---")
        print(f"{'Horse':16s}{'Win%':>6s}{'Place%':>7s}{'Fair':>7s}{'BF Back':>8s}{'EV@BF':>8s}  {'Drift':>5s}  {'Bet':9s}{'Stake':>16s}")
        for row in sub.iter_rows(named=True):
            bb, bl, ev = row["bf_back"], row["bf_lay"], row["edge_bf"]
            fair = row["fair_odds"]
            drift = row["drift_score"]
            place_prob = row["place_prob"]
            ew_edge = row["ew_edge"]
            bb_s = f"{bb:.2f}" if bb else "-"
            ev_s = f"{ev*100:+.1f}%" if ev is not None else "-"
            place_s = f"{place_prob*100:.0f}%" if place_prob is not None else "-"
            drift_s = "↓" if drift < -0.05 else ("↑" if drift > 0.05 else "–")
            act = _action(fair, bb, bl, drift)
            star = "★" if row["name"] in top_names and act in ("TAKE PRICE", "LAY") else " "
            if act == "TAKE PRICE" and ew_edge is not None and ew_edge > args.margin:
                bet = "EACH-WAY"
            else:
                bet = {"TAKE PRICE": "BACK WIN", "LAY": "LAY", "DRIFTER": "AVOID", "LEAVE": "-", "NO BF": "-"}[act]
            bet = f"{star}{bet}"
            print(f"{str(row['name'])[:16]:16s}{row['prob']*100:>5.1f}%{place_s:>7s}{fair:>7.2f}"
                  f"{bb_s:>8s}{ev_s:>8s}   {drift_s:>2s}  {bet:9s}{_stake(act, bl):>16s}")

    print("\nFair = 1/win% (model's true price).  Place% = model's top-2/3/4 probability.  BF Back = live Betfair exchange back.")
    print("Drift: ↓ = predicted to shorten, ↑ = predicted to drift, – = flat.")
    print(f"Bet = BACK WIN when BF Back >= Fair + {args.margin:.0%}; EACH-WAY when the place leg is also +EV; AVOID if predicted to drift > {args.drift_max:.0%}; LAY when BF Lay <= Fair - {args.margin:.0%}.")
    print(f"Stake = flat {args.stake_pct:.0f}% of £{args.bank:.0f} bank.  BACK uses that stake; LAY keeps the same LIABILITY (L£.., backer stake in brackets).")
    print(f"★ = the top {args.max_per_race} bet(s) per race (the ones to actually place).")

    # ---- log predictions to CSV (append, for later review / settling) ----
    import csv as _csv
    log_path = ROOT / "predictions_log.csv"
    new_file = not log_path.exists()
    with log_path.open("a", newline="") as f:
        w = _csv.writer(f)
        if new_file:
            w.writerow(["logged_at", "race_date", "course", "off_time", "race_id", "horse",
                        "win_pct", "fair", "bf_back", "bf_lay", "ev_bf_pct", "drift", "action"])
        for row in tod.sort(["off_time", "race_id"]).iter_rows(named=True):
            fair = row["fair_odds"]
            bb, bl = row["bf_back"], row["bf_lay"]
            drift = row["drift_score"]
            act = _action(fair, bb, bl, drift) if (fair and fair <= args.max_fair) else "DROPPED"
            w.writerow([
                dt.datetime.now().isoformat(timespec="seconds"), date_str,
                row["course_name"], row["off_time"], row["race_id"], row["name"],
                f"{row['prob']*100:.2f}", f"{fair:.2f}",
                f"{bb:.2f}" if bb else "", f"{bl:.2f}" if bl else "",
                f"{row['edge_bf']*100:+.2f}" if row["edge_bf"] is not None else "",
                f"{drift:+.3f}" if drift is not None else "",
                act,
            ])
    print(f"Logged {len(tod)} predictions to {log_path}")


if __name__ == "__main__":
    main()
