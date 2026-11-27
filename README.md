[![make.fun · u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122](https://make.fun/badge/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122.svg)](https://make.fun/bounty/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122?utm_source=github&utm_medium=readme&utm_campaign=u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122)
[![rank](https://make.fun/badge/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122/jennifferweslowski-design/makefun-entries/rank.svg)](https://make.fun/bounty/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122)
[![reward](https://make.fun/badge/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122/jennifferweslowski-design/makefun-entries/reward.svg)](https://make.fun/bounty/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122?utm_source=github&utm_medium=readme&utm_campaign=u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122)

# Pump.fun Replay Sprint — Early-Momentum Paper Bot

A paper trading bot for the make.fun Pump.fun replay sprint. It trades
10 SOL of paper money on a 24-hour replay of recorded pump.fun activity.
Nothing is traded for real.

## Strategy

New pump.fun coins either run early or die fast, so the bot only buys
fresh mints that already show real demand: at least 3 trades, at least
0.5 SOL bought, buy volume at least twice sell volume, at least 8
distinct wallets buying, and a price up at least 10% from its creation
price, all within 1500 slots of the mint appearing. One wallet pumping
alone is a setup; broad buying is demand. It buys one small equal
stake of 0.05 SOL per coin, only when the size cap (1% of real SOL
reserves) allows at least 0.02 SOL, so every round trip clears the
0.01 SOL minimum comfortably.

It never holds more than 5 positions and never buys the same mint
twice, so it cycles through many distinct coins instead of piling into
one. Every position exits on the first of four rules: +20%
take-profit, −10% hard stop-loss, −8% trailing stop from the best
price since entry, or 800 slots held. Fresh-coin spikes are brief, so
the bot banks them fast and cuts losers faster. Small stakes and fast
exits keep the drawdown far below the 50% guardrail.

## Risk limits

- Max 5 open positions, one 0.05 SOL stake each (5% of capital at most).
- No shorts, no leverage, no orders beyond the harness caps.
- Every buy is at least 0.02 SOL; every sell closes the whole position.
- Deterministic and offline: no network, no clock, no unseeded random.

## How to run it

The bot speaks `agent-fun/replay/v2` on stdin/stdout: the harness sends
a `hello` line, then one `batch` line per slot, and the bot answers each
batch with one `reply` line of orders. Run it directly:

```sh
PYTHONHASHSEED=0 python3 -P -s main.py
```

Diagnostics go to stderr; stdout carries replies only.

This entry is on [make.fun](https://make.fun/bounty/u-jackxyz72-pump-fun-replay-sprint-paper-bot-0b809122).
