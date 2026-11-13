# YC_Lunch

Static site for **YachtClubLunch.com**, deployed on Netlify from this repo.

- `index.html`: the home page
- `thanks.html`: shown after either form is sent
- `assets/`: the YCL burgee and the YCLB swallowtail (SVG)

Forms use Netlify Forms: `yclb-membership` and `station-suggestion`. Entries show up under Forms in the Netlify site dashboard.

Placeholders still to fill: `[AIR DAYS]`, `[YRR APP URL]`, `[PRIVACY URL]`, `[AFFILIATE EMAIL]`, `[AFFILIATE STATIONS…]`. Images live in `assets/`.

## Lunch Card Bingo

`bingo.html` deals each member a 4×4 card from `bingo/YYYY-MM-DD.json` (seeded by email + date). Calls arrive in Netlify Forms as `yclb-bingo`; check the winning line against that day's NextKast log.

Build a day's pool from the show hour's log:

    python3 tools/build_bingo_pool.py "D:/Dropbox/nextKast/Playlist/111326/12.pls" "D:/Dropbox/nextKast/masterLibrary.txt" 2026-11-13 > bingo/2026-11-13.json
    # Sunday Brunch: use 13.pls and add "Yacht Club Brunch" as a 4th argument

The published list mixes the hour's artists with library decoys, so it never gives the log away.
