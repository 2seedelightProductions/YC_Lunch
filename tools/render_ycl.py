#!/usr/bin/env python3
"""Render a Yacht Club Lunch archive from a NextKast hour log.

Usage: render_ycl.py <12.pls> <nextKast root> <MMDDYY> <out_dir> [--list-files]

- Cuts LegalIDs, network sweeps, commercials, Live365 ad breaks and promos.
- Keeps voice tracks, the open, YCL sweepers, Rock Block stingers, close and final message.
- Songs logged to start at 59:00 or later become bonus tracks; a YCL sweeper leads into them.
- Segues like the air chain: songs overlap the outgoing fade, voice tracks start
  over song tails, and songs start under the end of a voice track (talk-up, from IntroTime).
"""
import json, os, re, subprocess, sys, wave
import numpy as np

DROP_CATS = {"legalid", "network", "commercials", "promo", "yrrsweepers", "brb"}
BONUS_SWEEPERS = ["YCL_GonnaEatThat", "YCL_SoupDuJour", "YCL_NibbleOn", "YCL_3MealsADay", "YCL_GoodToEat"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def read_log(path):
    t = open(path, "rb").read().decode("cp1252", "replace")
    r = {}
    for line in t.splitlines():
        m = re.match(r"(File|Category|TrackName|TrackLengthSeconds|IntroTime)(\d+)=(.*)", line)
        if m:
            r.setdefault(int(m[2]), {})[m[1]] = m[3].strip()
    return [r[i] for i in sorted(r)]


def kind(e):
    c, n = e.get("Category", "").lower(), e.get("TrackName", "")
    if c in DROP_CATS or c.startswith("adbreak") or n.startswith(("Live365", "NostalgiAds", "WhamCo")):
        return None
    if n.startswith("VoiceTrack"):
        return "vt"
    if c in ("ycl sweepers", "ycl open"):
        return "sweep"
    if n.startswith("YRRB"):
        return "sting"
    if "chitm close" in c:
        return "bed"
    if c == "finalmessage":
        return "drop"
    return "song"


def plan(entries, root):
    t, items, used = 0.0, [], set()
    for e in entries:
        k = kind(e)
        if k:
            items.append({"kind": k, "file": e["File"], "name": e.get("TrackName", ""),
                          "cat": e.get("Category", ""), "intro": float(e.get("IntroTime", 0) or 0),
                          "bonus": k == "song" and t >= 59 * 60})
            if k == "sweep":
                used.add(os.path.splitext(os.path.basename(e["File"].replace("\\", "/")))[0])
        t += float(e.get("TrackLengthSeconds", 0) or 0)
    first = next((i for i, x in enumerate(items) if x["bonus"]), None)
    if first is not None and items[first - 1]["kind"] != "sweep":
        pick = next(s for s in BONUS_SWEEPERS if s not in used)
        items.insert(first, {"kind": "sweep", "file": root + "\\Music\\YCL Sweepers\\" + pick + ".mp3",
                             "name": pick, "cat": "YCL Sweepers", "intro": 0, "bonus": False, "bonus_lead": True})
    elif first is not None:
        items[first - 1]["bonus_lead"] = True
    return items


def local(win_path, staged_root):
    rel = win_path.split("nextKast\\", 1)[1].replace("\\", "/")
    p = os.path.join(staged_root, rel)
    if os.path.exists(p):
        return p
    # the track may have moved category folders since it aired
    base = os.path.basename(rel)
    for d, _, files in os.walk(os.path.join(staged_root, "Music")):
        if base in files:
            return os.path.join(d, base)
    raise FileNotFoundError(win_path)


def load(p):
    w = wave.open(p)
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
    return a


def audible_end(a, sr=44100, thr=-30):
    m = a.mean(1); h = int(sr * 0.1); k = len(m) // h
    if k == 0:
        return len(m) / sr
    e = 20 * np.log10(np.sqrt((m[:k * h].reshape(k, h) ** 2).mean(1) + 1e-12))
    loud = np.where(e > thr)[0]
    return (loud[-1] + 1) * 0.1 if len(loud) else len(m) / sr


def label(x):
    n = x["name"]; c = x["cat"].lower()
    pretty = n.replace(" - ", ", ", 1)
    if x.get("bonus"):
        return "Bonus track: " + pretty
    if c == "birthdaybeat":
        return "Birthday Beat: " + pretty
    if c == "deepdive":
        return "Deep Dive: " + pretty
    return pretty


def main():
    log, staged_root, mmddyy, out_dir = sys.argv[1:5]
    root = "D:\\Dropbox\\nextKast"
    items = plan(read_log(log), root)
    if "--list-files" in sys.argv:
        print(json.dumps(sorted({x["file"] for x in items})))
        return
    work = f"/tmp/render_{mmddyy}"; os.makedirs(work, exist_ok=True)
    lens, ends = [], []
    for n, x in enumerate(items):
        wav = f"{work}/{n:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "quiet", "-i", local(x["file"], staged_root),
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2", wav], check=True)
        a = load(wav); lens.append(len(a) / 44100); ends.append(audible_end(a))
    starts = [0.0]
    for n in range(1, len(items)):
        p, k, pk, ps = n - 1, items[n]["kind"], items[n - 1]["kind"], starts[n - 1]
        s = ps + ends[p]
        if pk == "song":
            s = ps + max(ends[p] - (3.0 if k == "song" else 4.0), lens[p] * 0.85)
        if pk == "vt" and k == "song":
            ov = min(max(items[n]["intro"] - 0.5, 0), 8.0, ends[p] - 3.0)
            s = ps + ends[p] - max(ov, 0)
        if pk in ("sweep", "sting", "drop", "bed"):
            s = ps + max(ends[p] - 0.4, 0)
        starts.append(s)
    mm, dd, yy = mmddyy[:2], mmddyy[2:4], mmddyy[4:]
    import datetime
    day = datetime.date(2000 + int(yy), int(mm), int(dd))
    title = f"Yacht Club Lunch, {DAYS[day.weekday()]} {day.strftime('%B')} {day.day}, {day.year}"
    out = f"{out_dir}/YCL-{mmddyy}.mp3"
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for n in range(len(items)):
        args += ["-i", f"{work}/{n:02d}.wav"]
    f = [f"[{n}:a]adelay={int(round(s*1000))}|{int(round(s*1000))}[a{n}]" for n, s in enumerate(starts)]
    f.append("".join(f"[a{n}]" for n in range(len(items))) +
             f"amix=inputs={len(items)}:normalize=0:dropout_transition=0,alimiter=limit=0.95:level=false[out]")
    args += ["-filter_complex", ";".join(f), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100",
             "-id3v2_version", "3", "-metadata", f"title={title}", "-metadata", "artist=Capt. Hugh",
             "-metadata", "album=Yacht Club Lunch", "-metadata", f"date={day.year}", "-metadata", "genre=Yacht Rock",
             "-metadata", "comment=yachtclublunch.com #YCLB", out]
    subprocess.run(args, check=True)
    rb, lines = 0, []
    for n, x in enumerate(items):
        if x["kind"] != "song":
            continue
        name = label(x)
        prev = items[n - 1]["name"] if n else ""
        if not x.get("bonus") and (prev.startswith("YRRB") or (n + 1 < len(items) and items[n + 1]["name"].startswith("YRRB_Mid"))):
            name = "Yacht Rock Rock Block: " + name
        s = starts[n]
        lines.append(f"{int(s//60):02d}:{int(s%60):02d}  {name}")
    total = max(s + l for s, l in zip(starts, lens))
    open(f"{out_dir}/YCL-{mmddyy}-tracklist.txt", "w").write(title + "\n\n" + "\n".join(lines) + "\n")
    print(title, f"{int(total//60)}:{int(total%60):02d}")


if __name__ == "__main__":
    main()
