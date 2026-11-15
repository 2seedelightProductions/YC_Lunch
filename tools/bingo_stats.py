#!/usr/bin/env python3
"""Summarize Music Lover Bingo activity for sponsor reports.

Export the two Netlify forms as CSV (Forms -> yclb-bingo-deal / yclb-bingo -> Export),
then run:

    python3 tools/bingo_stats.py --deals deals.csv [--calls calls.csv] [--from 2026-11-01 --to 2026-11-30]

Prints, per show and date: cards dealt, unique players, Bingo calls; plus totals and top cities.
"""
import argparse
import csv
from collections import Counter, defaultdict


def rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            yield {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}


def in_range(d, lo, hi):
    return (not lo or d >= lo) and (not hi or d <= hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deals", required=True, help="CSV export of the yclb-bingo-deal form")
    ap.add_argument("--calls", help="CSV export of the yclb-bingo form (Bingo calls)")
    ap.add_argument("--from", dest="lo", help="first date, YYYY-MM-DD")
    ap.add_argument("--to", dest="hi", help="last date, YYYY-MM-DD")
    a = ap.parse_args()

    dealt = Counter()
    players = defaultdict(set)
    all_players = set()
    cities = Counter()
    for r in rows(a.deals):
        d = r.get("date", "")
        if not d or not in_range(d, a.lo, a.hi):
            continue
        key = (d, r.get("show", ""))
        dealt[key] += 1
        p = r.get("player", "")
        if p:
            players[key].add(p)
            all_players.add(p)
        c = r.get("city", "").title()
        if c:
            cities[c] += 1

    calls = Counter()
    if a.calls:
        for r in rows(a.calls):
            # call form stores date as "YYYY-MM-DD (Show name)"
            raw = r.get("date", "")
            d, _, rest = raw.partition(" (")
            if not d or not in_range(d, a.lo, a.hi):
                continue
            calls[(d, rest.rstrip(")"))] += 1

    keys = sorted(set(dealt) | set(calls))
    print(f"{'Date':<11} {'Show':<34} {'Cards':>6} {'Players':>8} {'Calls':>6}")
    for k in keys:
        print(f"{k[0]:<11} {k[1][:34]:<34} {dealt[k]:>6} {len(players[k]):>8} {calls[k]:>6}")
    print("-" * 69)
    print(f"{'Total':<46} {sum(dealt.values()):>6} {len(all_players):>8} {sum(calls.values()):>6}")
    if cities:
        print("\nTop cities:")
        for c, n in cities.most_common(10):
            print(f"  {c:<30} {n}")


if __name__ == "__main__":
    main()
