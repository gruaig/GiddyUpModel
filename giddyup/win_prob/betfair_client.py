#!/usr/bin/env python3
"""Betfair exchange price client for horse-racing WIN markets (reuses tennisBot creds).

Fetches the live Betfair WIN market (best back / best lay) for today's GB/IRE
races and matches them to Sporting Life races by course + off time + horse name.

The exchange price has ~2% margin (vs ~15% for bookmakers), so this is the
"real" price to compare the model's fair price against.
"""
import datetime as dt
import re
import unicodedata
from typing import Dict, List, Optional

import pytz
from betfairlightweight import APIClient
from betfairlightweight.filters import market_filter, time_range, price_projection

USERNAME = "colfish"
PASSWORD = "Perlisagod$$1"
APP_KEY = "Gs1Zut6sZQxncj6V"

# Market names that are NOT the win market (place/exotic/special).
NON_WIN = re.compile(
    r"each\s*way|to\s*be\s*placed|\btbp\b|forecast|tricast|reverse|match\s*bet|"
    r"without|to\s*win\s*by|to\s*place|place\s*only|insurance",
    re.IGNORECASE,
)


COUNTRY_SUFFIX = re.compile(
    r"\s*\((IRE|GB|FR|USA|US|GER|AUS|NZ|SAF|ITY|SPA|JPN|ARG|BRZ|CHI|URU|POL|CZE|DEN|NOR|SWE|BEL|NED|SUI|AUT|HUN|SVK|TUR|UAE|KSA|QAT)\)\s*",
    re.IGNORECASE,
)


def norm(s):
    # strip Betfair country-code suffixes ("Horse (IRE)" -> "Horse"), fold diacritics
    # (é -> e), then drop everything non-alphanumeric.
    s = COUNTRY_SUFFIX.sub("", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def login() -> APIClient:
    client = APIClient(username=USERNAME, password=PASSWORD, app_key=APP_KEY)
    client.login_interactive()
    return client


def fetch_win_markets(client: APIClient, date_str: Optional[str] = None) -> List:
    """Return Betfair horse-racing WIN markets (catalogue + runner names).

    When date_str is given, fetch that whole day (00:00–24:00 UTC); otherwise the
    next 16 hours from now. This lets you predict tomorrow's card the evening before.
    """
    if date_str:
        start = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=pytz.UTC)
        end = start + dt.timedelta(days=1)
    else:
        start = dt.datetime.now(pytz.UTC)
        end = start + dt.timedelta(hours=16)
    cat = client.betting.list_market_catalogue(
        filter=market_filter(
            event_type_ids=["7"], in_play_only=False,
            market_start_time=time_range(from_=start.isoformat(), to=end.isoformat()),
        ),
        max_results=1000,
        market_projection=["EVENT", "RUNNER_DESCRIPTION", "MARKET_START_TIME"],
    )
    win = []
    for m in cat:
        if NON_WIN.search(m.market_name or ""):
            continue
        if not m.market_start_time:
            continue
        win.append(m)
    return win


def get_prices(client: APIClient, date_str: Optional[str] = None) -> List[dict]:
    """Return a flat list of win-market entries:
    [{event_name, off_time, market_name, runners:[{name, norm, selection_id, back, lay}]}]."""
    markets = fetch_win_markets(client, date_str)
    ids = [m.market_id for m in markets]
    books = {}
    import time as _t
    for i in range(0, len(ids), 10):
        chunk = ids[i:i + 10]
        try:
            for b in client.betting.list_market_book(chunk, price_projection(price_data=["EX_BEST_OFFERS"])):
                books[b.market_id] = b
        except Exception:
            for mid in chunk:
                try:
                    books[mid] = client.betting.list_market_book([mid], price_projection(price_data=["EX_BEST_OFFERS"]))[0]
                except Exception:
                    pass
        _t.sleep(0.6)  # polite throttle (Betfair rate limit ~10 calls/s)

    out = []
    for m in markets:
        st = m.market_start_time
        key = st.strftime("%H:%M") if isinstance(st, dt.datetime) else str(st)[11:16]
        runners = []
        for r in m.runners:
            row = {"name": r.runner_name, "norm": norm(r.runner_name), "selection_id": r.selection_id, "back": None, "lay": None}
            book = books.get(m.market_id)
            if book:
                for br in book.runners:
                    if br.selection_id == r.selection_id:
                        if br.ex.available_to_back:
                            row["back"] = br.ex.available_to_back[0].price
                        if br.ex.available_to_lay:
                            row["lay"] = br.ex.available_to_lay[0].price
                        break
            runners.append(row)
        out.append({"event_name": m.event.name or "", "off_time": key, "market_name": m.market_name or "", "runners": runners})
    return out


def match_race(prices: List[dict], course: str, off_time: str, tol_minutes: int = 150) -> Optional[List[dict]]:
    """Find the Betfair win market for a SL course + off time (HH:MM)."""
    cn = norm(course)
    if not cn:
        return None
    try:
        target = dt.datetime.strptime(off_time, "%H:%M")
    except Exception:
        return None
    best = None
    best_diff = None
    for m in prices:
        if cn not in norm(m["event_name"]):
            continue
        try:
            kt = dt.datetime.strptime(m["off_time"], "%H:%M")
        except Exception:
            continue
        diff = abs((kt - target).total_seconds()) / 60
        if diff > tol_minutes:
            continue
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best = m["runners"]
    return best


def runner_price(betfair_runners: Optional[List[dict]], horse_name: str):
    """Return (back, lay, selection_id) for a horse, matching by normalized name."""
    if not betfair_runners:
        return None, None, None
    hn = norm(horse_name)
    for r in betfair_runners:
        if r["norm"] == hn:
            return r["back"], r["lay"], r["selection_id"]
    return None, None, None


if __name__ == "__main__":
    c = login()
    print("Logged in.")
    p = get_prices(c)
    print(f"Win markets fetched: {len(p)}")
    # demo: match Fairyhouse 12:30
    for course, t in [("Fairyhouse", "12:30"), ("Huntingdon", "13:10"), ("Lingfield", "12:45")]:
        runners = match_race(p, course, t)
        if runners:
            print(f"\n{course} {t}: {len(runners)} runners")
            for r in runners[:5]:
                print(f"   {r['name']:24s} back={r['back']} lay={r['lay']}")
        else:
            print(f"\n{course} {t}: NO MATCH")
    c.logout()
