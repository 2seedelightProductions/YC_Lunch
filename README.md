# YC_Lunch

Static site for **YachtClubLunch.com**, deployed on Netlify from this repo.

- `index.html`: the home page
- `thanks.html`: shown after either form is sent
- `assets/`: the YCL burgee and the YCLB swallowtail (SVG)

Forms use Netlify Forms: `yclb-membership` and `station-suggestion`. Entries show up under Forms in the Netlify site dashboard.

Placeholders still to fill: `[AIR DAYS]`, `[YRR APP URL]`, `[PRIVACY URL]`, `[AFFILIATE EMAIL]`, `[AFFILIATE STATIONS…]`. Images live in `assets/`.

## Lunch Card Bingo

`bingo.html` deals each member a 4×4 card from `bingo/YYYY-MM-DD.json` (seeded by email + date). Calls arrive in Netlify Forms as `yclb-bingo`; check the winning line against that day's NextKast log.

Build a day's pool from the show's logs (weekday Lunch = H12, 4×4 card; Sunday Brunch = H10–H13, 5×5 card with free center and four corners):

    python3 tools/build_bingo_pool.py --lib "D:/Dropbox/nextKast/masterLibrary.txt" --date 2026-11-13 "D:/Dropbox/nextKast/Playlist/111326/12.pls" > bingo/2026-11-13.json
    python3 tools/build_bingo_pool.py --lib ... --date 2026-11-15 --brunch .../111526/10.pls .../11.pls .../12.pls .../13.pls > bingo/2026-11-15.json

Live only: cards deal 15 minutes before the show; Bingo can be called during the show and for 15 minutes after (Lunch 11:45–1:15 ET, Brunch 9:45–2:15 ET). First timestamped call that checks out wins.

The published list mixes the hour's artists with library decoys, so it never gives the log away.
