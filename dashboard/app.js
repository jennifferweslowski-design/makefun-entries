// Token Radar dashboard (model radar-2). Reads window.RADAR (written beside dashboard/ by main.ts)
// and renders the ranked board, filters, a per-protocol detail view with the model's own inputs and
// the protocol's farm plan, plus the live-token set at market values. No network: every byte it
// shows is in data.js. State lives in the URL hash, so #detail=<slug>, #category=<name>,
// #chain=<name>, #q=<text>, #tab=live and #sort=<key> all render deterministically.
(function () {
  'use strict';

  var DATA = window.RADAR;
  var app = document.getElementById('board');
  if (!DATA || !app) return;
  app.removeAttribute('aria-busy');

  var MODEL = DATA.model;
  var state = { q: '', category: 'all', chain: 'all', tab: 'pre-token', sort: 'implied', dir: -1, selected: null };

  var usd0 = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
  function fmtUsd(n) {
    if (n === null || n === undefined || !isFinite(n)) return 'n/a';
    if (Math.abs(n) >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B';
    if (Math.abs(n) >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (Math.abs(n) >= 1e3) return '$' + Math.round(n / 1e3) + 'K';
    return usd0.format(n);
  }
  function fmtMult(n) { return (n === null || n === undefined || !isFinite(n)) ? 'n/a' : n.toFixed(3) + 'x'; }
  function fmtPct(n) {
    if (n === null || n === undefined || !isFinite(n)) return 'n/a';
    return (n > 0 ? '+' : '') + n.toFixed(2) + '%';
  }
  function pctCls(n) { return (n === null || n === undefined) ? 'na' : (n > 0 ? 'pos' : (n < 0 ? 'neg' : 'na')); }
  function fmtAge(days) {
    if (days === null || days === undefined) return 'unknown';
    if (days >= 365) return (days / 365).toFixed(1) + 'y';
    return Math.max(0, Math.round(days)) + 'd';
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  // The model, recomputed in the page from the same figures board.json carries, so the page's
  // arithmetic and the board's number are visibly the same: implied = TVL x category multiple
  // x growth multiplier x maturity multiplier, rounded.
  function impliedOf(row) {
    var growth = Math.min(MODEL.growth_cap, Math.max(MODEL.growth_floor, row.change_7d === null || row.change_7d === undefined ? 0 : row.change_7d));
    var growthMult = 1 + (growth / 100) * MODEL.growth_weight;
    var age = row.age_days === null || row.age_days === undefined ? MODEL.unknown_age_days : row.age_days;
    var maturity = MODEL.maturity_floor + (Math.min(Math.max(age, 0), MODEL.maturity_days) / MODEL.maturity_days) * MODEL.maturity_range;
    return Math.max(1, Math.round(row.base_value_usd * growthMult * maturity));
  }

  function readHash() {
    var h = location.hash.replace(/^#/, '');
    var out = {};
    h.split('&').forEach(function (part) {
      var kv = part.split('=');
      if (kv[0]) out[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1] || '');
    });
    return out;
  }
  function writeHash() {
    var parts = [];
    if (state.q) parts.push('q=' + encodeURIComponent(state.q));
    if (state.category !== 'all') parts.push('category=' + encodeURIComponent(state.category));
    if (state.chain !== 'all') parts.push('chain=' + encodeURIComponent(state.chain));
    if (state.tab !== 'pre-token') parts.push('tab=' + encodeURIComponent(state.tab));
    if (state.sort !== 'implied' || state.dir !== -1) parts.push('sort=' + encodeURIComponent(state.sort + ':' + (state.dir === 1 ? 'asc' : 'desc')));
    if (state.selected) parts.push('detail=' + encodeURIComponent(state.selected));
    var h = parts.join('&');
    if (('' + location.hash.replace(/^#/, '')) !== h) history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
  }
  function applyHash() {
    // A hash navigation fully defines the state: a key that is absent resets
    // to its default, so a filtered view never inherits a stale selection.
    var h = readHash();
    state.q = h.q || '';
    state.category = h.category || 'all';
    state.chain = h.chain || 'all';
    state.tab = h.tab || 'pre-token';
    state.sort = 'implied';
    state.dir = -1;
    if (h.sort !== undefined) {
      var sp = h.sort.split(':');
      state.sort = sp[0] || 'implied';
      state.dir = sp[1] === 'asc' ? 1 : -1;
    }
    state.selected = h.detail || null;
  }

  function categories() {
    var seen = {};
    DATA.rows.forEach(function (r) { if (r.category) seen[r.category] = true; });
    return Object.keys(seen).sort();
  }
  function chains() {
    var seen = {};
    DATA.rows.forEach(function (r) { (r.chains || []).forEach(function (c) { seen[c] = true; }); });
    return Object.keys(seen).sort();
  }

  function filteredRows() {
    var q = state.q.trim().toLowerCase();
    var rows = DATA.rows.filter(function (r) {
      if (state.category !== 'all' && r.category !== state.category) return false;
      if (state.chain !== 'all' && (r.chains || []).indexOf(state.chain) < 0) return false;
      if (q && (r.name + ' ' + r.slug + ' ' + (r.category || '')).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    var key = state.sort;
    var dir = state.dir;
    function val(r) {
      if (key === 'implied') return r.implied_value_usd;
      if (key === 'tvl') return r.tvl_usd;
      if (key === 'growth') return r.change_7d === null ? -Infinity : r.change_7d;
      if (key === 'age') return r.age_days === null ? -1 : r.age_days;
      if (key === 'name') return r.name.toLowerCase();
      return r.rank;
    }
    rows.sort(function (a, b) {
      var va = val(a), vb = val(b);
      if (va < vb) return -dir;
      if (va > vb) return dir;
      return a.rank - b.rank;
    });
    return rows;
  }

  function el(tag, attrs) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'class') node.className = attrs[k];
        else if (k === 'text') node.textContent = attrs[k];
        else if (k === 'html') node.innerHTML = attrs[k];
        else if (k.slice(0, 2) === 'on') node.addEventListener(k.slice(2), attrs[k]);
        else if (attrs[k] !== null && attrs[k] !== undefined) node.setAttribute(k, attrs[k]);
      });
    }
    for (var i = 2; i < arguments.length; i++) {
      var child = arguments[i];
      if (child === null || child === undefined) continue;
      if (Array.isArray(child)) child.forEach(function (c) { if (c) node.appendChild(c); });
      else if (typeof child === 'string') node.appendChild(document.createTextNode(child));
      else node.appendChild(child);
    }
    return node;
  }

  function statCard(k, v, d) {
    return el('div', { class: 'stat' }, el('div', { class: 'k', text: k }), el('div', { class: 'v', html: v }), el('div', { class: 'd', text: d }));
  }

  function renderDetail(row) {
    var checked = impliedOf(row) === row.implied_value_usd;
    var growth = Math.min(MODEL.growth_cap, Math.max(MODEL.growth_floor, row.change_7d === null ? 0 : row.change_7d));
    var growthMult = 1 + (growth / 100) * MODEL.growth_weight;
    var age = row.age_days === null ? MODEL.unknown_age_days : row.age_days;
    var comp = row.comparables > 0
      ? row.comparables + ' live ' + (row.category || 'uncategorised') + ' protocols set the multiple'
      : 'fewer than ' + MODEL.min_comparables + ' live comparables in this category, so the global median applies';
    var wrap = el('section', { class: 'detail', id: 'detail' },
      el('h2', { text: '#' + row.rank + '  ' + row.name }),
      el('p', { class: 'dsub', text: (row.category || 'Uncategorised') + '  ·  ' + (row.chains || []).join(', ') + '  ·  tracked since ' + (row.listed_at || 'unknown') + '  ·  records no token' }),
      el('div', { class: 'dgrid' },
        statCard('Implied value', esc(fmtUsd(row.implied_value_usd)), checked ? 'page recomputes the same number' : 'page recomputes ' + fmtUsd(impliedOf(row))),
        statCard('TVL', esc(fmtUsd(row.tvl_usd)), '7d ' + fmtPct(row.change_7d)),
        statCard('Category multiple', esc(fmtMult(row.category_multiple)), comp),
        statCard('Age without a token', esc(fmtAge(row.age_days)), 'maturity multiplier ' + row.maturity_multiplier.toFixed(3) + 'x')),
      el('h3', { text: 'How the value is built' }),
      el('table', { class: 'model' }, el('tbody', null,
        el('tr', null, el('td', { text: 'TVL' }), el('td', { text: fmtUsd(row.tvl_usd) })),
        el('tr', null, el('td', { text: 'x category multiple (' + comp + ')' }), el('td', { text: fmtMult(row.category_multiple) })),
        el('tr', null, el('td', { text: '= base value' }), el('td', { text: fmtUsd(row.base_value_usd) })),
        el('tr', null, el('td', { text: 'x growth multiplier (' + fmtPct(row.change_7d) + ' over 7 days, clamped to ' + MODEL.growth_floor + '%..' + MODEL.growth_cap + '%)' }), el('td', { text: growthMult.toFixed(3) + 'x' })),
        el('tr', null, el('td', { text: 'x maturity multiplier (' + fmtAge(row.age_days) + ' running with no token)' }), el('td', { text: row.maturity_multiplier.toFixed(3) + 'x' })),
        el('tr', { class: 'total' }, el('td', { text: '= implied value' }), el('td', { text: fmtUsd(row.implied_value_usd) })))),
      el('h3', { text: 'How to farm it' }),
      el('ol', { class: 'steps' }, row.farm_steps.map(function (s) { return el('li', { text: s }); })));
    return wrap;
  }

  function render() {
    app.innerHTML = '';
    var wrap = el('div', { class: 'wrap' });
    var top = DATA.rows[0];
    wrap.appendChild(el('header', null,
      el('h1', { html: 'Token Radar<span class="dot">.</span>' }),
      el('p', { class: 'sub', text: 'Pre-token protocols ranked by implied launch value — and what to do to farm each one.' }),
      el('p', { class: 'meta', html: 'Snapshot <b>' + esc(DATA.as_of) + '</b> · source: DefiLlama public API · model <b>' + esc(DATA.model_version) + '</b> · ' + DATA.board_size + ' rows · watchlist ' + DATA.watchlist_size + '/' + DATA.watchlist_size + ' covered' })));
    wrap.appendChild(el('div', { class: 'stats' },
      statCard('Protocols ranked', String(DATA.board_size), DATA.early_size + ' below the watchlist floor'),
      statCard('Watchlist covered', DATA.watchlist_size + ' / ' + DATA.watchlist_size, 'every protocol on the floor is ranked'),
      statCard('Global median multiple', fmtMult(DATA.global_multiple), 'market cap / TVL across live protocols'),
      statCard('Top implied value', esc(fmtUsd(top ? top.implied_value_usd : 0)), top ? top.name : '')));
    wrap.appendChild(el('div', { class: 'method' },
      el('p', { html: '<b>How a row is priced.</b> Each category\u2019s base multiple is the median market-cap-to-TVL ratio of that category\u2019s live-token protocols in this same snapshot (at least ' + MODEL.min_comparables + ' comparables, else the global median), clamped to ' + MODEL.multiple_floor + 'x–' + MODEL.multiple_cap + 'x. Implied value = TVL \u00d7 multiple \u00d7 growth \u00d7 maturity, where growth is the 7-day TVL change clamped to ' + MODEL.growth_floor + '%–' + MODEL.growth_cap + '% and maturity rises with the days a protocol has run with no token.' }),
      el('p', { text: 'Wrapped, staked and bridged products of tokens that already trade are set aside, not ranked: their token exists. The board separates protocols whose token already trades from those still to come.' })));

    var controls = el('div', { class: 'controls' });
    var qInput = el('input', { type: 'search', placeholder: 'Search a protocol\u2026', value: state.q, 'aria-label': 'Search protocols' });
    qInput.addEventListener('input', function () { state.q = qInput.value; writeHash(); render(); });
    var catSel = el('select', { 'aria-label': 'Filter by category' });
    catSel.appendChild(el('option', { value: 'all', text: 'All categories' }));
    categories().forEach(function (c) { catSel.appendChild(el('option', { value: c, text: c })); });
    catSel.value = state.category;
    catSel.addEventListener('change', function () { state.category = catSel.value; writeHash(); render(); });
    var chainSel = el('select', { 'aria-label': 'Filter by chain' });
    chainSel.appendChild(el('option', { value: 'all', text: 'All chains' }));
    chains().forEach(function (c) { chainSel.appendChild(el('option', { value: c, text: c })); });
    chainSel.value = state.chain;
    chainSel.addEventListener('change', function () { state.chain = chainSel.value; writeHash(); render(); });
    var sortSel = el('select', { 'aria-label': 'Sort by' });
    [['implied', 'Sort: implied value'], ['tvl', 'Sort: TVL'], ['growth', 'Sort: 7-day change'], ['age', 'Sort: age'], ['name', 'Sort: name']].forEach(function (o) {
      sortSel.appendChild(el('option', { value: o[0], text: o[1] }));
    });
    sortSel.value = state.sort;
    sortSel.addEventListener('change', function () { state.sort = sortSel.value; writeHash(); render(); });
    var tabs = el('div', { class: 'tabs' });
    var tabPre = el('button', { class: 'tab' + (state.tab === 'pre-token' ? ' on' : ''), text: 'Pre-token board (' + DATA.board_size + ')' });
    tabPre.addEventListener('click', function () { state.tab = 'pre-token'; state.selected = null; writeHash(); render(); });
    var tabLive = el('button', { class: 'tab' + (state.tab === 'live' ? ' on' : ''), text: 'Live tokens (' + DATA.live.length + ')' });
    tabLive.addEventListener('click', function () { state.tab = 'live'; state.selected = null; writeHash(); render(); });
    tabs.appendChild(tabPre);
    tabs.appendChild(tabLive);
    controls.appendChild(qInput);
    controls.appendChild(catSel);
    controls.appendChild(chainSel);
    controls.appendChild(sortSel);
    controls.appendChild(tabs);
    wrap.appendChild(controls);

    if (state.tab === 'live') {
      wrap.appendChild(el('p', { class: 'count', text: 'Protocols whose token already trades, by market cap. Their values are the market\u2019s own, not the model\u2019s — they are the comparables the multiples are calibrated on.' }));
      var lt = el('table', null);
      lt.appendChild(el('thead', null, el('tr', null,
        el('th', { text: 'Protocol' }), el('th', { text: 'Category' }), el('th', { class: 'num', text: 'TVL' }),
        el('th', { class: 'num', text: 'Market cap' }), el('th', { class: 'num', text: '7d' }), el('th', { class: 'num', text: 'Mcap / TVL' }))));
      var lb = el('tbody', null);
      DATA.live.forEach(function (p) {
        lb.appendChild(el('tr', null,
          el('td', { class: 'name', html: esc(p.name) }),
          el('td', { class: 'cat', text: p.category || '—' }),
          el('td', { class: 'num', text: fmtUsd(p.tvl_usd) }),
          el('td', { class: 'num', text: fmtUsd(p.mcap_usd) }),
          el('td', { class: 'num ' + pctCls(p.change_7d), text: fmtPct(p.change_7d) }),
          el('td', { class: 'num', text: (p.mcap_usd && p.tvl_usd) ? (p.mcap_usd / p.tvl_usd).toFixed(3) + 'x' : 'n/a' })));
      });
      lt.appendChild(lb);
      wrap.appendChild(lt);
    } else {
      var rows = filteredRows();
      wrap.appendChild(el('p', { class: 'count', text: rows.length + ' of ' + DATA.board_size + ' protocols shown · click a row for its value breakdown and farm plan' }));
      if (state.selected) {
        var sel = null;
        DATA.rows.forEach(function (r) { if (r.slug === state.selected) sel = r; });
        if (sel) wrap.appendChild(renderDetail(sel));
      }
      var table = el('table', null);
      var head = el('tr', null);
      [['rank', 'Rank'], ['name', 'Protocol'], ['cat', 'Category'], ['chains', 'Chains'], ['tvl', 'TVL'], ['growth', '7d'], ['implied', 'Implied value'], ['age', 'Age']].forEach(function (c) {
        var arrow = state.sort === c[0] ? (state.dir === 1 ? ' ▲' : ' ▼') : '';
        head.appendChild(el('th', { class: (c[0] === 'tvl' || c[0] === 'growth' || c[0] === 'implied' || c[0] === 'rank') ? 'num' : '', text: c[1] + arrow,
          onclick: function () {
            if (state.sort === c[0]) state.dir = -state.dir;
            else { state.sort = c[0]; state.dir = (c[0] === 'name' ? 1 : -1); }
            writeHash(); render();
          } }));
      });
      table.appendChild(el('thead', null, head));
      var tb = el('tbody', null);
      if (rows.length === 0) {
        tb.appendChild(el('tr', null, el('td', { colspan: '8', class: 'empty', text: 'No protocol matches this filter.' })));
      }
      rows.forEach(function (r) {
        var tr = el('tr', { class: state.selected === r.slug ? 'sel' : '' });
        tr.addEventListener('click', function () {
          state.selected = state.selected === r.slug ? null : r.slug;
          writeHash(); render();
          if (state.selected) { var d = document.getElementById('detail'); if (d) d.scrollIntoView({ block: 'start' }); }
        });
        tr.appendChild(el('td', { class: 'rank num', text: String(r.rank) }));
        tr.appendChild(el('td', { class: 'name', html: esc(r.name) + '<span class="slug">' + esc(r.slug) + '</span>' }));
        tr.appendChild(el('td', { class: 'cat', text: r.category || '—' }));
        var ch = el('td', { class: 'chains' });
        (r.chains || []).slice(0, 3).forEach(function (c) { ch.appendChild(el('span', { class: 'pill', text: c })); });
        if ((r.chains || []).length > 3) ch.appendChild(el('span', { class: 'pill', text: '+' + ((r.chains || []).length - 3) }));
        tr.appendChild(ch);
        tr.appendChild(el('td', { class: 'num', text: fmtUsd(r.tvl_usd) }));
        tr.appendChild(el('td', { class: 'num ' + pctCls(r.change_7d), text: fmtPct(r.change_7d) }));
        tr.appendChild(el('td', { class: 'num', text: fmtUsd(r.implied_value_usd) }));
        tr.appendChild(el('td', { class: 'num', text: fmtAge(r.age_days) }));
        tb.appendChild(tr);
      });
      table.appendChild(tb);
      wrap.appendChild(table);
    }

    wrap.appendChild(el('footer', null,
      el('p', { text: 'Implied values are this entry\u2019s own claim, never make.fun\u2019s: a board\u2019s implied value is what the protocol\u2019s record would be worth if it launched a token at its category\u2019s market multiple. It does not predict whether or when a token is issued.' }),
      el('p', { text: 'A protocol that records no token may still have one its DefiLlama record does not carry. Farm plans are suggestions, not advice: check the protocol\u2019s own pages before moving funds.' })));
    app.appendChild(wrap);
  }

  applyHash();
  render();
  window.addEventListener('hashchange', function () { applyHash(); render(); });
})();
