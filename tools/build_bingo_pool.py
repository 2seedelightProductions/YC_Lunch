#!/usr/bin/env python3
"""Build a bingo pool for Yacht Club Lunch (weekday H12, 4x4 card) or
Yacht Club Brunch (Sunday H10-H13, 5x5 card) from the NextKast hour logs.

Usage:
  python3 build_bingo_pool.py --lib masterLibrary.txt --date 2026-11-13 Playlist/111326/12.pls > bingo/2026-11-13.json
  python3 build_bingo_pool.py --lib masterLibrary.txt --date 2026-11-15 --brunch \
      Playlist/111526/10.pls Playlist/111526/11.pls Playlist/111526/12.pls Playlist/111526/13.pls > bingo/2026-11-15.json

The published list mixes the scheduled artists with library decoys, so it never
gives the log away. Cards are drawn in the browser, seeded by email + date.
Winners are checked against the logs, which never go on the site.
"""
import argparse, json, random, re, sys
from collections import Counter

NON_MUSIC = {
    "", "legalid", "ycl open", "ycl sweepers", "network", "commercials",
    "adbreak120", "promo", "voicetracks", "finalmessage", "ycb sweepers",
    "yrrsweepers", "brb", "features", "specialty",
}
DECOY_CATS = {"yachtrock", "yachtiest", "am gold", "retro", "yarandb", "smoothfm"}

SHOWS = {
    "lunch": {
        "show": "Yacht Club Lunch", "size": 4,
        "deal_from": "11:45", "show_start": "12:00", "show_end": "13:00", "call_until": "13:15",
        "moments": ["The Birthday Beat", "A Deep Dive", "Yacht Rock Rock Block",
                    "Capt. Hugh says “Studio Sea”", "702-YR-YACHT",
                    "A YCLB birthday shout-out", "Capt. Hugh’s Final Thought"],
    },
    "brunch": {
        "show": "Yacht Club Brunch", "size": 5,
        "deal_from": "09:45", "show_start": "10:00", "show_end": "14:00", "call_until": "14:15",
        "moments": ["The Birthday Beat", "A Deep Dive", "Yacht Rock Rock Block",
                    "Capt. Hugh says “Studio Sea”", "Capt. Hugh’s Final Thought"],
    },
}


def artist_of(name):
    if " - " not in name:
        return ""
    a = name.split(" - ", 1)[0].strip()
    if a.lower().endswith(", the"):
        a = "The " + a[:-5].strip()
    return a


def hour_artists(path):
    text = open(path, "rb").read().decode("cp1252", "replace")
    cats, names = {}, {}
    for line in text.splitlines():
        m = re.match(r"(Category|TrackName)(\d+)=(.*)", line)
        if m:
            (cats if m[1] == "Category" else names)[int(m[2])] = m[3].strip()
    out = []
    for i in sorted(names):
        c, n = cats.get(i, "").lower(), names[i]
        if c in NON_MUSIC or c.startswith("adbreak") or c.endswith(".mp3"):
            continue
        if n.startswith(("VoiceTrack", "YCL_", "YRRB", "Live365", "NostalgiAds", "WhamCo", "Voice Guy")):
            continue
        a = artist_of(n)
        if a and a not in out:
            out.append(a)
    return out


def library_artists(path):
    counts = Counter()
    for rec in open(path, "rb").read().split(b"\x00"):
        f = rec.decode("cp1252", "replace").split("^^")
        if len(f) < 3 or "\\Music\\" not in f[2]:
            continue
        cat = f[2].split("\\Music\\", 1)[1].split("\\", 1)[0].lower()
        fname = f[2].rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        a = artist_of(fname)
        if cat in DECOY_CATS and a and "duplicate" not in fname.lower():
            counts[a] += 1
    return [a for a, n in counts.items() if n >= 3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--brunch", action="store_true")
    ap.add_argument("logs", nargs="+")
    a = ap.parse_args()
    cfg = dict(SHOWS["brunch" if a.brunch else "lunch"])
    real = []
    for p in a.logs:
        for x in hour_artists(p):
            if x not in real:
                real.append(x)
    lower = {x.lower() for x in real}
    pool = [x for x in library_artists(a.lib) if x.lower() not in lower]
    random.Random(a.date).shuffle(pool)
    decoys = pool[: max(len(real), 10)]
    cfg.update({"date": a.date, "artists": sorted(real + decoys, key=str.lower)})
    json.dump(cfg, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
