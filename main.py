"""Pump.fun replay sprint paper bot: early momentum, tight exits.

Speaks agent-fun/replay/v2 on stdin/stdout: one JSON line in per batch,
one reply line out. No network, no files, no clock, no unseeded random:
the same input always produces the same orders.

Strategy, in short:
  * Watch every new mint. A mint becomes a buy candidate once it shows
    real early demand: at least 3 trades, at least 0.5 SOL bought, buy
    volume at least twice sell volume, at least 8 distinct wallets
    buying, and its price up at least 10% from its creation price,
    all within 1500 slots of the mint appearing. One wallet pumping
    alone is a setup; broad buying is demand.
  * Buy one small equal stake (0.05 SOL) per mint, only when the size cap
    (1% of real SOL reserves) allows at least 0.02 SOL, so every round
    trip clears the 0.01 SOL minimum by a wide margin.
  * Hold at most 5 positions at once and never buy a mint twice, so the
    bot cycles through many distinct coins instead of piling into one.
  * Exit every position on the first of: +20% take-profit, -10% hard
    stop-loss, -8% trailing stop from the best price since entry, or
    800 slots held. Fresh-coin spikes are brief, so the bot banks them
    fast and cuts losers faster. Small stakes and fast exits keep the
    drawdown far below the 50% guardrail.
"""

import json
import re
import sys

PROTOCOL = "agent-fun/replay/v2"
LAMPORTS_PER_SOL = 1_000_000_000

# --- sizing ---
STAKE_LAMPORTS = 50_000_000          # 0.05 SOL per position
MIN_CAP_LAMPORTS = 20_000_000       # only buy when the size cap allows this
MIN_BUY_LAMPORTS = 10_000_000       # guardrail minimum per round trip
MAX_SLIPPAGE_BPS = 1000             # 10% slippage tolerance

# --- entry filter ---
ENTRY_MIN_TRADES = 3
ENTRY_MIN_RISE_BPS = 1000          # price up 10% from creation price
ENTRY_MIN_BUY_SOL = 500_000_000   # at least 0.5 SOL of buys seen already
ENTRY_BUY_SELL_RATIO = 2           # buy volume at least 2x sell volume
ENTRY_MIN_BUYERS = 8               # at least 8 distinct wallets buying
ENTRY_MAX_AGE_SLOTS = 1500          # only fresh mints

# --- exits (basis points against the entry price, or the peak) ---
TAKE_PROFIT_BPS = 2000              # +20%: spikes are brief, bank them
STOP_LOSS_BPS = 1000                # -10%: cut losers fast
TRAIL_BPS = 800                     # -8% from the best price since entry
MAX_HOLD_SLOTS = 800

_MINT_RE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
_CLIENT_RE = re.compile(r"[A-Za-z0-9-][A-Za-z0-9_-]{0,63}")


def log(msg):
    print(msg, file=sys.stderr, flush=True)


class Curve:
    """Latest known reserves and early-trade stats for one mint."""

    __slots__ = (
        "mint", "created_slot", "create_price", "reserves_slot",
        "virtual_token", "virtual_quote", "real_token", "real_quote",
        "complete", "trades", "buy_sol", "sell_sol", "buyers",
    )

    def __init__(self, mint, slot):
        self.mint = mint
        self.created_slot = slot
        self.create_price = 0.0
        self.reserves_slot = slot
        self.virtual_token = 0
        self.virtual_quote = 0
        self.real_token = 0
        self.real_quote = 0
        self.complete = False
        self.trades = 0
        self.buy_sol = 0
        self.sell_sol = 0
        # Distinct wallets that bought: a spike driven by many wallets is
        # real demand; one wallet buying alone is usually a setup.
        self.buyers = set()

    def price(self):
        if self.virtual_token <= 0:
            return 0.0
        return self.virtual_quote / self.virtual_token


class Bot:
    def __init__(self, hello):
        self.hello = hello
        self.caps = hello["caps"]
        self.fees = hello["fees"]
        self.cash = int(hello["capital"]["lamports"])
        self.slot = -1
        self.seq = -1
        # mint -> (token_amount, cost_lamports)
        self.positions = {}
        # mint -> Curve, first-seen order
        self.curves = {}
        # mint -> (entry_slot, entry_price, peak_price)
        self.entries = {}
        # mints already bought once (membership only, never iterated)
        self.decided = set()
        # fresh mints still young enough to consider (mint -> None, insertion order)
        self.candidates = {}
        # client_id -> (side, mint)
        self.pending = {}
        self._next_id = 1
        self.batches = 0
        self.buys_sent = 0
        self.sells_sent = 0

    def tx_fee(self):
        return int(self.fees["base_fee_lamports"]) + int(self.fees["priority_fee_lamports"])

    def next_client_id(self):
        cid = "o%d" % self._next_id
        self._next_id += 1
        return cid

    def curve_for(self, mint, slot):
        curve = self.curves.get(mint)
        if curve is None:
            curve = Curve(mint, slot)
            self.curves[mint] = curve
        return curve

    def free_cash(self):
        free = self.cash
        for side, _mint in self.pending.values():
            free -= self.tx_fee()
            if side == "buy":
                free -= STAKE_LAMPORTS
        return free

    def committed_mints(self):
        mints = set(self.positions)
        for side, mint in self.pending.values():
            if side == "buy":
                mints.add(mint)
        return mints

    def max_buy(self, mint):
        curve = self.curves.get(mint)
        if curve is None or curve.complete:
            return 0
        bps = self.caps["max_order_bps_of_real_reserve"]
        return curve.real_quote * bps // 10000

    def apply_batch(self, batch):
        self.seq = batch["seq"]
        self.slot = batch["slot"]
        # Fills first: clear pending, and let a rejected buy be retried later.
        for fill in batch["fills"]:
            cid = fill["client_id"]
            pending = self.pending.pop(cid, None)
            if pending is not None and pending[0] == "buy" and fill["status"] != "filled":
                self.decided.discard(pending[1])
        # Account: cash and positions as the harness reports them.
        account = batch["account"]
        self.cash = int(account["cash_lamports"])
        new_positions = {}
        for pos in account["positions"]:
            tokens = int(pos["token_amount"])
            if tokens > 0:
                new_positions[pos["mint"]] = (tokens, int(pos["cost_lamports"]))
        for mint, (tokens, cost) in new_positions.items():
            if mint not in self.positions and mint not in self.entries:
                entry_price = cost / tokens if tokens else 0.0
                self.entries[mint] = (self.slot, entry_price, entry_price)
        for mint in list(self.entries):
            if mint not in new_positions:
                del self.entries[mint]
        self.positions = new_positions
        # Marks: latest reserves, only when newer than what we hold.
        for mark in batch["marks"]:
            curve = self.curves.get(mark["mint"])
            if curve is not None and mark["slot"] < curve.reserves_slot:
                continue
            if curve is None:
                curve = self.curve_for(mark["mint"], mark["slot"])
            curve.virtual_token = int(mark["virtual_token_reserves"])
            curve.virtual_quote = int(mark["virtual_quote_reserves"])
            curve.real_token = int(mark["real_token_reserves"])
            curve.real_quote = int(mark["real_quote_reserves"])
            curve.reserves_slot = mark["slot"]
        # Events, in order.
        for event in batch["events"]:
            kind = event["event"]
            mint = event["mint"]
            if kind == "CreateEvent":
                curve = self.curve_for(mint, event["slot"])
                self.candidates[mint] = None
                curve.created_slot = event["slot"]
                curve.virtual_token = int(event["virtual_token_reserves"])
                curve.virtual_quote = int(event["virtual_sol_reserves"])
                curve.real_token = int(event["real_token_reserves"])
                curve.real_quote = 0
                curve.reserves_slot = event["slot"]
                curve.create_price = curve.price()
            elif kind == "TradeEvent":
                curve = self.curve_for(mint, event["slot"])
                if mint not in self.candidates and mint not in self.decided:
                    self.candidates[mint] = None
                curve.virtual_token = int(event["virtual_token_reserves"])
                curve.virtual_quote = int(event["virtual_sol_reserves"])
                curve.real_token = int(event["real_token_reserves"])
                curve.real_quote = int(event["real_sol_reserves"])
                curve.reserves_slot = event["slot"]
                curve.trades += 1
                amount = int(event["sol_amount"])
                if event["is_buy"]:
                    curve.buy_sol += amount
                    curve.buyers.add(event["user"])
                else:
                    curve.sell_sol += amount
                if curve.create_price == 0.0:
                    curve.create_price = curve.price()
            else:  # CompleteEvent
                curve = self.curve_for(mint, event["slot"])
                curve.complete = True

    def decide(self):
        orders = []
        max_orders = self.caps["max_orders_per_batch"]
        # --- exits first: free a slot before deciding new buys ---
        pending_sell_mints = {
            mint for side, mint in self.pending.values() if side == "sell"
        }
        for mint in list(self.positions):
            if len(orders) >= max_orders:
                break
            if mint in pending_sell_mints:
                continue
            curve = self.curves.get(mint)
            if curve is None or curve.complete:
                continue
            entry = self.entries.get(mint)
            if entry is None:
                continue
            entry_slot, entry_price, peak = entry
            price = curve.price()
            if price <= 0.0 or entry_price <= 0.0:
                continue
            if price > peak:
                self.entries[mint] = (entry_slot, entry_price, price)
                peak = price
            rise_bps = int((price - entry_price) * 10000 / entry_price)
            trail_bps = int((price - peak) * 10000 / peak) if peak > 0 else 0
            age = self.slot - entry_slot
            should_sell = (
                rise_bps >= TAKE_PROFIT_BPS
                or rise_bps <= -STOP_LOSS_BPS
                or trail_bps <= -TRAIL_BPS
                or age >= MAX_HOLD_SLOTS
            )
            if not should_sell:
                continue
            tokens, _cost = self.positions[mint]
            if tokens <= 0:
                continue
            orders.append({
                "side": "sell",
                "client_id": self.next_client_id(),
                "mint": mint,
                "token_amount": str(tokens),
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            })
        # --- entries: fresh mints with early buy momentum ---
        # Prune the candidate list first so each batch only scans young mints.
        committed = self.committed_mints()
        for mint in list(self.candidates):
            curve = self.curves.get(mint)
            if (
                curve is None
                or curve.complete
                or mint in self.decided
                or mint in committed
                or self.slot - curve.created_slot > ENTRY_MAX_AGE_SLOTS
            ):
                del self.candidates[mint]
        open_slots = self.caps["max_open_positions"] - len(committed)
        free = self.free_cash()
        tx = self.tx_fee()
        for mint in list(self.candidates):
            curve = self.curves[mint]
            if len(orders) >= max_orders or open_slots <= 0:
                break
            if curve.trades < ENTRY_MIN_TRADES:
                continue
            if curve.buy_sol < ENTRY_MIN_BUY_SOL:
                continue
            if curve.buy_sol < ENTRY_BUY_SELL_RATIO * curve.sell_sol:
                continue
            if len(curve.buyers) < ENTRY_MIN_BUYERS:
                continue
            if curve.create_price <= 0.0:
                continue
            price = curve.price()
            if price <= 0.0:
                continue
            rise_bps = int((price - curve.create_price) * 10000 / curve.create_price)
            if rise_bps < ENTRY_MIN_RISE_BPS:
                continue
            cap = self.max_buy(mint)
            if cap < MIN_CAP_LAMPORTS:
                continue
            amount = min(cap, STAKE_LAMPORTS)
            if amount < MIN_BUY_LAMPORTS:
                continue
            if free < amount + tx:
                continue
            if not _MINT_RE.fullmatch(mint):
                continue
            orders.append({
                "side": "buy",
                "client_id": self.next_client_id(),
                "mint": mint,
                "quote_lamports": str(amount),
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            })
            self.decided.add(mint)
            curve.buyers.clear()
            del self.candidates[mint]
            committed.add(mint)
            open_slots -= 1
            free -= amount + tx
        return orders

    def record_orders(self, orders):
        for order in orders:
            self.pending[order["client_id"]] = (order["side"], order["mint"])
            if order["side"] == "buy":
                self.buys_sent += 1
            else:
                self.sells_sent += 1


def check_order(order):
    side = order.get("side")
    if side not in ("buy", "sell"):
        raise ValueError("bad side: %r" % (side,))
    if not _CLIENT_RE.fullmatch(order.get("client_id", "")):
        raise ValueError("bad client_id: %r" % (order.get("client_id"),))
    if not _MINT_RE.fullmatch(order.get("mint", "")):
        raise ValueError("bad mint: %r" % (order.get("mint"),))
    amount_key = "quote_lamports" if side == "buy" else "token_amount"
    amount = order.get(amount_key)
    if not isinstance(amount, str) or not amount.isdigit() or int(amount) <= 0:
        raise ValueError("bad %s: %r" % (amount_key, amount))
    bps = order.get("max_slippage_bps")
    if type(bps) is not int or not 0 <= bps <= 10000:
        raise ValueError("bad max_slippage_bps: %r" % (bps,))
    allowed = {"side", "client_id", "mint", amount_key, "max_slippage_bps"}
    if set(order) != allowed:
        raise ValueError("unexpected order keys: %r" % (sorted(order),))


def main():
    bot = None
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            raise SystemExit("input line is not JSON: %r" % line[:80])
        kind = msg.get("type") if isinstance(msg, dict) else None
        if kind == "hello":
            if bot is not None:
                raise SystemExit("second hello")
            if msg.get("protocol") != PROTOCOL:
                raise SystemExit("unknown protocol: %r" % (msg.get("protocol"),))
            bot = Bot(msg)
            log("hello: capital %s lamports, max %d positions, latency %d slots"
                % (msg["capital"]["lamports"],
                   msg["caps"]["max_open_positions"],
                   msg["latency_slots"]))
        elif kind == "batch":
            if bot is None:
                raise SystemExit("batch before hello")
            bot.apply_batch(msg)
            orders = bot.decide()
            for order in orders:
                check_order(order)
            if len(orders) > bot.caps["max_orders_per_batch"]:
                raise SystemExit("too many orders in one batch reply")
            bot.record_orders(orders)
            reply = json.dumps(
                {"type": "reply", "seq": msg["seq"], "orders": orders},
                separators=(",", ":"), ensure_ascii=False)
            if len(reply.encode("utf-8")) > 65536:
                raise SystemExit("reply over 64 KiB")
            out.write(reply + "\n")
            out.flush()
            bot.batches += 1
        elif kind == "done":
            if bot is None:
                raise SystemExit("done before hello")
            log("done: %d batches, %d buys, %d sells, cash %d lamports, "
                "%d open positions"
                % (bot.batches, bot.buys_sent, bot.sells_sent,
                   bot.cash, len(bot.positions)))
            return 0
        else:
            raise SystemExit("unknown message type: %r" % (kind,))
    raise SystemExit("input ended before done")


if __name__ == "__main__":
    sys.exit(main())
