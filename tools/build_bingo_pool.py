#!/usr/bin/env python3
"""Build a Yacht Club Lunch bingo pool from a NextKast hour log.

Usage:
  python3 build_bingo_pool.py <hour.pls> <masterLibrary.txt> <YYYY-MM-DD> [show name] > bingo/<YYYY-MM-DD>.json

Works for Yacht Club Lunch (weekday H12) and Yacht Club Brunch (Sunday H13).

Reads the noon-hour .pls (cp1252), finds the music that airs, and picks
decoy artists from the library that are NOT in the hour, then publishes one
mixed list. Cards are drawn in the browser, seeded by email + date. Winners
are checked against the hour's log, which never goes on the site.
"""
import json, random, re, sys
from collections import Counter

NON_MUSIC = {
    "", "legalid", "ycl open", "ycl sweepers", "network", "commercials",
    "adbreak120", "promo", "voicetracks", "finalmessage", "ycb sweepers",
    "yrrsweepers", "brb", "features", "specialty",
}
DECOY_CATS = {"yachtrock", "yachtiest", "am gold", "retro", "yarandb", "smoothfm"}


def artist_of(name):
    if " - " not in name:
        return ""
    a = name.split(" - ", 1)[0].strip()
    if a.lower().endswith(", the"):
        a = "The " + a[:-5].strip()
    return a


def read_hour(path):
    text = open(path, "rb").read().decode("cp1252", "replace")
    cats, names = {}, {}
    for line in text.splitlines():
        m = re.match(r"(Category|TrackName)(\d+)=(.*)", line)
        if m:
            (cats if m[1] == "Category" else names)[int(m[2])] = m[3].strip()
    rows = [(i, cats.get(i, ""), names.get(i, "")) for i in sorted(names)]
    music, birthday, deepdive, rockblock = [], None, None, []
    for idx, (i, cat, name) in enumerate(rows):
        c = cat.lower()
        if c in NON_MUSIC or c.endswith(".mp3") or name.startswith(("VoiceTrack", "YCL_", "YRRB", "Live365", "NostalgiAds")):
            continue
        a = artist_of(name)
        if not a:
            continue
        music.append({"artist": a, "title": name.split(" - ", 1)[1].strip(), "category": cat})
        if c == "birthdaybeat":
            birthday = a
        if c == "deepdive":
            deepdive = a
    # Yacht Rock Rock Block = song before YRRB_Mid, song between Mid and Wrap, song after Wrap
    for idx, (i, cat, name) in enumerate(rows):
        if name.startswith(("YRRB_Mid", "YRRB_Wrap")):
            for j in (idx - 1, idx + 1):
                if 0 <= j < len(rows) and artist_of(rows[j][2]) and not rows[j][2].startswith(("VoiceTrack", "YCL_", "YRRB")):
                    a = artist_of(rows[j][2])
                    if a not in rockblock:
                        rockblock.append(a)
    return music, birthday, deepdive, rockblock


def read_library(path):
    data = open(path, "rb").read()
    counts = Counter()
    for rec in data.split(b"\x00"):
        f = rec.decode("cp1252", "replace").split("^^")
        if len(f) < 3:
            continue
        name, path = f[0], f[2]
        # NextKast keeps the category as the folder under ...\Music\
        cat = path.split("\\Music\\", 1)[1].split("\\", 1)[0].lower() if "\\Music\\" in path else ""
        # the file name keeps the "Artist - Title" form even when the tag doesn't
        fname = path.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        a = artist_of(fname)
        if cat in DECOY_CATS and a and "duplicate" not in fname.lower():
            counts[a] += 1
    return [a for a, n in counts.items() if n >= 3]


def main():
    hour, lib, date = sys.argv[1:4]
    show = sys.argv[4] if len(sys.argv) > 4 else "Yacht Club Lunch"
    music, birthday, deepdive, rockblock = read_hour(hour)
    hour_artists = []
    for m in music:
        if m["artist"] not in hour_artists:
            hour_artists.append(m["artist"])
    lower = {a.lower() for a in hour_artists}
    pool = [a for a in read_library(lib) if a.lower() not in lower]
    random.Random(date).shuffle(pool)
    # Publish one mixed, alphabetized list so nobody can tell scheduled artists from decoys.
    decoys = pool[: max(len(hour_artists), 10)]
    out = {
        "date": date,
        "show": show,
        "artists": sorted(hour_artists + decoys, key=str.lower),
        "moments": [
            "The Birthday Beat",
            "A Deep Dive",
            "Yacht Rock Rock Block",
            "Capt. Hugh says \u201cStudio Sea\u201d",
            "702-YR-YACHT",
            "A YCLB birthday shout-out",
        ],
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
