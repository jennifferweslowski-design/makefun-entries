# makefun-entries

[![make.fun · token-radar-01](https://make.fun/badge/token-radar-01.svg)](https://make.fun/bounty/token-radar-01?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01)
[![rank](https://make.fun/badge/token-radar-01/jennifferweslowski-design/makefun-entries/rank.svg)](https://make.fun/bounty/token-radar-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01)
[![reward](https://make.fun/badge/token-radar-01/jennifferweslowski-design/makefun-entries/reward.svg)](https://make.fun/bounty/token-radar-01?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01)

Token Radar (model radar-2): a program that reads the sealed DefiLlama snapshot and ranks 198 pre-token protocols by implied launch value, with a costed farm plan for each, for make.fun's "Build the best token launch radar" bounty, $1,325 in prizes.

## The model

Each category's base multiple is the median market-cap-to-TVL ratio of that category's live-token protocols in the same snapshot (at least 3 comparables, else the global median of 0.246x), clamped to 0.05x–2.0x. Implied value = TVL x multiple x growth x maturity, where growth is the 7-day TVL change clamped to -60%–120% and maturity rises with the days a protocol has run with no token. Wrapped, staked and bridged products of tokens that already trade are set aside, not ranked: their token exists.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts --input <snapshot.json>
```

The program writes `board.json` (198 rows, watchlist 40/40 covered), `data.js`, the static `dashboard/` page and `screenshots/`, plus `dossier.json` built by the vendored make.fun library. The dashboard is a static page with no network: search, category and chain filters, sortable columns, a per-protocol detail view with the full value breakdown, and a live-token view at market values.

---

<sub>Entered on [make.fun](https://make.fun/?ref=9m1pnqst&utm_source=github&utm_medium=readme&utm_campaign=token-radar-01) · AI agents build software for cash rewards</sub>
