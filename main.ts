// early-riser: a momentum bot for the pump.fun paper sprint (agent-fun/replay/v2).
//
// Idea: on a 6-hour window, most new pump.fun coins bleed out, but a few catch a bid
// early and run. This bot only buys coins that have already proved they can rise:
// a coin becomes a candidate once its price is up 8% from where its curve opened,
// with at least 8 trades behind it, and the price still sitting near
// its own recent high (no chasing a coin that already dumped from its peak). Each
// buy is a fixed 0.25 SOL stake (capped at 1% of the coin's real SOL reserve, per
// the rules), one buy per coin, at most 5 open positions. Every position exits on
// the first of: +20% take-profit, -7% stop-loss, an 8% trailing stop from its best
// price since entry, or 5,400 slots (~36 minutes) held, so capital keeps rotating
// onto fresh coins and the bot clears the 20-coin breadth bar with room to spare.
//
// Deterministic by construction: every decision comes only from the batch stream
// (slots, reserves, fills). No clock, no environment, no randomness.

import { LAMPORTS_PER_SOL, runBot, type BotState, type Batch, type OrderInput } from './vendor/makefun-bot.ts';

// ---- tuning (all in whole units so the logic reads plainly) -----------------

const STAKE_LAMPORTS = LAMPORTS_PER_SOL / 4n; // 0.25 SOL per buy
const MIN_BUY_LAMPORTS = LAMPORTS_PER_SOL / 50n; // 0.02 SOL: never buy dust
const MAX_SLIPPAGE_BPS = 5000;
const MIN_TRADES = 8; // need real activity before trusting a rise
const RISE_BPS = 10800; // price must be >= 108% of its opening price (bps, 10000 = 1x)
const NEAR_PEAK_BPS = 9700; // ...and within 3% of its own recent high
const MIN_BUY_AGE_SLOTS = 0; // no age floor: the early pop is the signal, and the trade-count and near-peak checks already filter the noisiest launches
const MAX_BUY_AGE_SLOTS = 14400; // only buy coins younger than ~96 minutes
const TAKE_PROFIT_BPS = 12000; // sell at +20% over entry
const STOP_LOSS_BPS = 9300; // sell at -7% under entry
const TRAILING_BPS = 9200; // sell at -8% under the best price since entry: pump coins spike then dump, so bank the peak early
const MAX_HOLD_SLOTS = 5400; // sell after ~36 minutes held, whatever the price did

// ---- per-coin tape ----------------------------------------------------------

interface Tape {
  openPrice: number; // SOL per token when the curve opened (from CreateEvent)
  peakPrice: number; // highest price seen since the curve opened
  trades: number; // TradeEvents seen on this curve
  firstSlot: number; // slot the curve was first seen
  bought: boolean; // a buy was already decided for this coin
}

interface Entry {
  entryPrice: number; // price when the buy was decided
  peakPrice: number; // best price since entry
  buySlot: number; // slot the buy was decided on
}

/** Price of a curve in SOL per token, from its virtual reserves. 0 when unknown. */
function priceOf(state: BotState, mint: string): number {
  const curve = state.curves.get(mint);
  if (curve === undefined) return 0;
  const tokens = Number(curve.virtual_token_reserves);
  const quote = Number(curve.virtual_quote_reserves);
  if (tokens <= 0 || quote <= 0) return 0;
  return quote / tokens;
}

const tapes = new Map<string, Tape>();
const entries = new Map<string, Entry>();
const pendingBuys = new Map<string, { mint: string; entryPrice: number }>();
const pendingSells = new Map<string, string>(); // client_id -> mint
let buySeq = 0;
let sellSeq = 0;

await runBot({
  onBatch(state, batch) {
    const orders: OrderInput[] = [];

    // Fold this batch's fills first: a buy that was rejected or failed frees the
    // coin up for another try, and a filled sell confirms the position is gone.
    // A sell that was rejected or failed leaves the entry in place so the next
    // batch tries the exit again instead of orphaning the position.
    for (const fill of batch.fills) {
      const pending = pendingBuys.get(fill.client_id);
      if (pending !== undefined) {
        pendingBuys.delete(fill.client_id);
        if (fill.status !== 'filled') {
          const tape = tapes.get(pending.mint);
          if (tape !== undefined) tape.bought = false;
          entries.delete(pending.mint);
        }
        continue;
      }
      const soldMint = pendingSells.get(fill.client_id);
      if (soldMint !== undefined) {
        pendingSells.delete(fill.client_id);
        if (fill.status === 'filled') entries.delete(soldMint);
      }
    }

    // Update the tape from this batch's events.
    for (const event of batch.events) {
      if (event.event === 'CreateEvent') {
        const tokens = Number(event.virtual_token_reserves);
        const quote = Number(event.virtual_sol_reserves);
        const open = tokens > 0 && quote > 0 ? quote / tokens : 0;
        tapes.set(event.mint, {
          openPrice: open,
          peakPrice: open,
          trades: 0,
          firstSlot: event.slot,
          bought: false,
        });
      } else if (event.event === 'TradeEvent') {
        let tape = tapes.get(event.mint);
        if (tape === undefined) {
          tape = { openPrice: 0, peakPrice: 0, trades: 0, firstSlot: event.slot, bought: false };
          tapes.set(event.mint, tape);
        }
        tape.trades += 1;
        const price = priceOf(state, event.mint);
        if (price > 0) {
          if (tape.openPrice === 0) tape.openPrice = price;
          if (price > tape.peakPrice) tape.peakPrice = price;
        }
      } else {
        // CompleteEvent: the curve is done; forget its tape so nothing buys it.
        tapes.delete(event.mint);
        entries.delete(event.mint);
      }
    }

    // Refresh each open position's peak price from the latest reserves.
    for (const [mint, entry] of entries) {
      const price = priceOf(state, mint);
      if (price > entry.peakPrice) entry.peakPrice = price;
    }

    // Exits first: free a slot before deciding new buys.
    for (const [mint, holding] of state.positions) {
      const entry = entries.get(mint);
      const price = priceOf(state, mint);
      if (entry === undefined || price <= 0) continue;
      const up = (price / entry.entryPrice) * 10000;
      const offPeak = (price / entry.peakPrice) * 10000;
      const heldSlots = batch.slot - entry.buySlot;
      const shouldSell =
        up >= TAKE_PROFIT_BPS ||
        up <= STOP_LOSS_BPS ||
        offPeak <= TRAILING_BPS ||
        heldSlots >= MAX_HOLD_SLOTS;
      if (!shouldSell) continue;
      sellSeq += 1;
      const sellId = `sell${sellSeq}`;
      pendingSells.set(sellId, mint);
      orders.push({
        side: 'sell',
        client_id: sellId,
        mint,
        token_amount: holding.token_amount,
        max_slippage_bps: MAX_SLIPPAGE_BPS,
      });
    }

    // Entries: scan this batch's events in order; at most one buy per coin ever.
    const freeSlots = state.hello.caps.max_open_positions - state.committedPositionCount();
    let buysLeft = Math.max(0, freeSlots);
    if (buysLeft > 0) {
      const txFee = state.txFeeLamports();
      for (const event of batch.events) {
        if (buysLeft <= 0) break;
        if (event.event !== 'TradeEvent' && event.event !== 'CreateEvent') continue;
        const mint = event.mint;
        const tape = tapes.get(mint);
        const curve = state.curves.get(mint);
        if (tape === undefined || curve === undefined || curve.complete) continue;
        if (tape.bought || state.positions.has(mint)) continue;
        if (tape.trades < MIN_TRADES) continue;
        if (tape.openPrice <= 0) continue;
        const ageSlots = batch.slot - tape.firstSlot;
        if (ageSlots < MIN_BUY_AGE_SLOTS) continue;
        if (ageSlots > MAX_BUY_AGE_SLOTS) continue;
        const price = priceOf(state, mint);
        if (price <= 0) continue;
        const rise = (price / tape.openPrice) * 10000;
        if (rise < RISE_BPS) continue;
        const nearPeak = (price / tape.peakPrice) * 10000;
        if (nearPeak < NEAR_PEAK_BPS) continue;
        const cap = state.maxBuyLamports(mint);
        const amount = cap < STAKE_LAMPORTS ? cap : STAKE_LAMPORTS;
        if (amount < MIN_BUY_LAMPORTS) continue;
        if (state.freeCashLamports() - txFee < amount) continue;

        buySeq += 1;
        const clientId = `buy${buySeq}`;
        pendingBuys.set(clientId, { mint, entryPrice: price });
        entries.set(mint, { entryPrice: price, peakPrice: price, buySlot: batch.slot });
        tape.bought = true;
        orders.push({
          side: 'buy',
          client_id: clientId,
          mint,
          quote_lamports: amount,
          max_slippage_bps: MAX_SLIPPAGE_BPS,
        });
        buysLeft -= 1;
      }
    }

    return orders;
  },

  onDone(state, done) {
    const cash = Number(done.account.cash_lamports) / Number(LAMPORTS_PER_SOL);
    console.error(
      `done: cash ${cash.toFixed(4)} SOL, positions left ${done.account.positions.length}, ` +
        `coins bought ${buySeq}, batches ${state.seq}`,
    );
  },
});
