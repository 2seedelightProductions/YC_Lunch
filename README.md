# YC_Lunch

Static site for **YachtClubLunch.com**, deployed on Netlify from this repo.

- `index.html`: the home page
- `thanks.html`: shown after either form is sent
- `assets/`: the YCL burgee and the YCLB swallowtail (SVG)

Forms use Netlify Forms: `yclb-membership` and `station-suggestion`. Entries show up under Forms in the Netlify site dashboard.

Placeholders still to fill: `[AIR DAYS]`, `[YRR APP URL]`, `[PRIVACY URL]`, `[AFFILIATE EMAIL]`, `[AFFILIATE STATIONS…]`. Images live in `assets/`.

## Music Lover Bingo

`bingo.html` deals each member a 4×4 card from `bingo/YYYY-MM-DD.json` (seeded by email + date). Calls arrive in Netlify Forms as `yclb-bingo`; check the winning line against that day's NextKast log.

Every card dealt also posts an anonymous entry to the `yclb-bingo-deal` form (date, show, city, a random per-browser player id, time dealt; no name or email). For sponsor numbers, export both forms as CSV from Netlify and run:

    python3 tools/bingo_stats.py --deals deals.csv --calls calls.csv --from 2026-11-01 --to 2026-11-30

It prints cards dealt, unique players and Bingo calls per show and date, plus top cities.

Build a day's pool from the show's logs (weekday Lunch = H12, 4×4 card; Sunday Brunch = H10–H13, 5×5 card with free center and four corners):

    python3 tools/build_bingo_pool.py --lib "D:/Dropbox/nextKast/masterLibrary.txt" --date 2026-11-13 "D:/Dropbox/nextKast/Playlist/111326/12.pls" > bingo/2026-11-13.json
    python3 tools/build_bingo_pool.py --lib ... --date 2026-11-15 --brunch .../111526/10.pls .../11.pls .../12.pls .../13.pls > bingo/2026-11-15.json

Bingo cards are valid 15 minutes before and after each program: Lunch at noon and its midnight re-air (11:45 a.m.–1:15 p.m. and 11:45 p.m.–1:15 a.m. ET, a fresh card for each), Brunch 9:45 a.m.–2:15 p.m. ET. First timestamped call that checks out wins station merch.

The published list mixes the hour's artists with library decoys, so it never gives the log away.
