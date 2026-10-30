// Stock panel: one stock against its sector peers, opened on top of any view.

import { createChart, base, valueAxis, tooltip, tooltipHtml, tokens, disposeCharts } from './charts.js';
import { cap, date, esc, pct, tone, value } from './format.js';
import { labelTag, legend } from './components.js';
import { slugify } from './store.js';
import { closeStock } from './router.js';
import { isNum } from './stats.js';

const PEER_METRICS = [
  'forward_pe', 'ev_to_ebitda', 'fcf_yield', 'roe', 'profit_margin', 'revenue_growth',
  'debt_to_equity', 'interest_coverage', '1y_return', 'volatility', 'sharpe_ratio',
  'quality_score', 'technical_score', 'analyst_upside',
];

const TAGS = [
  ['valuation_category', ''],
  ['performance_category', ''],
  ['technical_signal', 'Technical'],
  ['z_score_zone', 'Altman Z'],
];

const drawer = document.getElementById('drawer');
const panel = drawer.querySelector('.drawer-panel');
const body = drawer.querySelector('.drawer-body');
let current = null;
let returnFocus = null;

drawer.addEventListener('click', (e) => {
  if (e.target.closest('[data-close]')) closeStock();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && current) closeStock();
});

function close() {
  if (!current) return;
  current = null;
  drawer.classList.remove('open');
  drawer.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  disposeCharts(drawer);
  returnFocus?.focus?.({ preventScroll: true });
}

export function renderStock(ds, ticker) {
  const stock = ticker ? ds.byTicker.get(ticker) : null;
  if (!stock) return close();
  if (current === ticker && drawer.classList.contains('open')) return;

  if (!current) returnFocus = document.activeElement;
  current = ticker;
  disposeCharts(drawer);
  body.innerHTML = content(ds, stock);
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  panel.scrollTop = 0;
  panel.focus({ preventScroll: true });

  if (ds.history) renderPrice(ds, stock);
}

function content(ds, s) {
  const r1y = s['1y_return'];
  const index = s.index === 'S&P500' ? 'S&P 500' : s.index === 'NASDAQ100' ? 'Nasdaq-100' : s.index;
  return `
    <header class="stock-head">
      <div class="eyebrow">
        <a href="#/sector/${slugify(s.sector)}">${esc(s.sector)}</a>
        ${s.industry ? `<span>${esc(s.industry)}</span>` : ''}
        ${index ? `<span>${esc(index)}</span>` : ''}
      </div>
      <h2>${esc(s.name)} <span class="symbol">${esc(s.ticker)}</span></h2>
      <div class="stock-price">
        <span class="price">${esc(value(ds.metric('current_price'), s.current_price))}</span>
        ${isNum(r1y) ? `<span class="${tone(r1y)}">${esc(pct(r1y, { signed: true }))} over 1 year</span>` : ''}
        <span class="muted">Market cap ${esc(cap(s.market_cap))}</span>
      </div>
      <div class="stock-tags">${TAGS.filter(([k]) => s[k]).map(([k, prefix]) => labelTag(k, s[k], { prefix })).join('')}</div>
    </header>

    ${ds.history ? `<section class="section">
      <div class="section-head"><h2>Price vs sector</h2><p>Weekly closes over two years, rebased to the first week.</p></div>
      ${legend([{ color: 'var(--accent)', label: s.ticker, kind: 'line' }, { color: 'var(--context)', label: `${s.sector} index`, kind: 'line' }])}
      <div class="chart" data-chart="price" style="height:240px;margin-top:6px"></div>
    </section>` : ''}

    <section class="section">
      <div class="section-head"><h2>Versus sector peers</h2>
        <p>Percentile among the ${ds.peers(s.sector).length} ${esc(s.sector)} stocks. Bars run right when the stock is better than the sector median, left when worse.</p></div>
      ${peerBars(ds, s)}
    </section>

    ${analystTargets(ds, s)}

    <section class="section">
      <div class="section-head"><h2>All metrics</h2></div>
      ${facts(ds, s)}
    </section>`;
}

const ordinal = (n) => {
  const teen = n % 100 >= 11 && n % 100 <= 13;
  return `${n}${teen ? 'th' : { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'}`;
};

function peerBars(ds, s) {
  const peers = ds.peers(s.sector);
  const rows = PEER_METRICS.map((k) => ds.metric(k))
    .filter((m) => m && m.better && isNum(s[m.key]))
    .map((m) => {
      const p = ds.favourability(s, m.key, peers);
      if (!isNum(p)) return '';
      const left = Math.min(p, 50);
      const width = Math.abs(p - 50);
      const color = p >= 50 ? 'var(--pos)' : 'var(--neg)';
      return `<span class="label" title="${esc(m.description)}">${esc(m.label)}</span>
        <span class="peer-track" title="${ordinal(Math.round(p))} percentile (higher is more favourable)">
          <span class="fill" style="left:${left}%;width:${width}%;background:${color}"></span>
          <span class="median" style="left:50%"></span></span>
        <span class="value">${esc(value(m, s[m.key], { signed: m.signed }))}</span>`;
    });
  return `<div class="peer-bars">${rows.join('')}</div>`;
}

function analystTargets(ds, s) {
  const { target_low_price: low, target_mean_price: mean, target_high_price: high, current_price: price } = s;
  if (![low, mean, high, price].every(isNum) || high <= low) return '';
  const lo = Math.min(low, price);
  const hi = Math.max(high, price);
  const at = (v) => `${((v - lo) / (hi - lo)) * 100}%`;
  const m = ds.metric('current_price');
  const upside = mean / price - 1;
  const analysts = isNum(s.number_of_analyst_opinions) ? ` from ${s.number_of_analyst_opinions} analysts` : '';
  return `<section class="section">
    <div class="section-head"><h2>Analyst price targets</h2>
      <p>Mean target ${esc(value(m, mean))} (<span class="${tone(upside)}">${esc(pct(upside, { signed: true }))}</span>)${esc(analysts)}.</p></div>
    ${legend([{ color: 'var(--ink)', label: `Price ${value(m, price)}`, kind: 'line' }, { color: 'var(--accent)', label: `Mean target ${value(m, mean)}`, kind: 'line' }])}
    <div class="range" role="img" aria-label="Price targets from ${esc(value(m, low))} to ${esc(value(m, high))}">
      <span class="rail" style="left:${at(low)};right:calc(100% - ${at(high)})"></span>
      <span class="mark current" style="left:${at(price)}"></span>
      <span class="mark target" style="left:${at(mean)}"></span>
      <span class="label start" style="left:${at(low)}">Low ${esc(value(m, low))}</span>
      <span class="label end" style="left:${at(high)}">High ${esc(value(m, high))}</span>
    </div></section>`;
}

function facts(ds, s) {
  const shown = new Set(['current_price', 'market_cap', 'target_low_price', 'target_mean_price', 'target_high_price', ...TAGS.map(([k]) => k)]);
  const groups = new Map();
  for (const m of ds.metrics) {
    if (shown.has(m.key) || s[m.key] === null || s[m.key] === undefined) continue;
    if (!groups.has(m.group)) groups.set(m.group, []);
    groups.get(m.group).push(m);
  }
  return `<div class="facts">${[...groups]
    .map(([group, ms]) => `<h4>${esc(group)}</h4>${ms
      .map((m) => `<div class="fact" title="${esc(m.description)}"><span>${esc(m.label)}</span><span>${esc(value(m, s[m.key], { signed: m.signed }))}</span></div>`)
      .join('')}`)
    .join('')}</div>`;
}

async function renderPrice(ds, stock) {
  const el = body.querySelector('[data-chart="price"]');
  const prices = await ds.prices();
  if (current !== stock.ticker || !el.isConnected) return;
  const closes = prices?.prices?.[stock.ticker];
  if (!closes) {
    el.outerHTML = '<p class="note">Weekly prices are not available for this stock.</p>';
    return;
  }

  // Sector index sampled at the weekly dates (last trading day on or before each)
  const daily = ds.history.dates;
  const sectorDaily = ds.sectorSeries(stock.sector, 'cap');
  let j = 0;
  const sectorWeekly = prices.dates.map((d) => {
    while (j + 1 < daily.length && daily[j + 1] <= d) j += 1;
    return daily[j] <= d ? sectorDaily[j] : null;
  });

  const first = closes.findIndex(isNum);
  const rebase = (xs) => {
    const b = xs[first];
    return xs.map((v, i) => (i >= first && isNum(v) && isNum(b) ? v / b - 1 : null));
  };
  const stockPath = rebase(closes);
  const sectorPath = rebase(sectorWeekly);
  const t = tokens();
  const m = ds.metric('current_price');

  createChart(el).setOption({
    ...base(t),
    grid: { left: 4, right: 12, top: 10, bottom: 4, containLabel: true },
    xAxis: {
      type: 'category', data: prices.dates, boundaryGap: false,
      axisLine: { lineStyle: { color: t.axis } }, axisTick: { show: false },
      axisLabel: { color: t.muted, fontSize: 11, formatter: (d) => date(d), hideOverlap: true, alignMinLabel: 'left', alignMaxLabel: 'right' },
    },
    yAxis: valueAxis(t, { metric: { fmt: 'pct' }, scale: true, splitNumber: 4 }),
    tooltip: tooltip(t, {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: t.axis } },
      formatter: (ps) => {
        const i = ps[0].dataIndex;
        return tooltipHtml(`Week of ${date(ps[0].axisValue)}`, [
          ...ps.map((p) => [p.color, p.seriesName, pct(p.value, { signed: true })]),
          [null, 'Close', value(m, closes[i])],
        ]);
      },
    }),
    series: [
      { name: `${stock.sector} index`, type: 'line', data: sectorPath, symbol: 'none', color: t.context, lineStyle: { width: 1.5 } },
      { name: stock.ticker, type: 'line', data: stockPath, symbol: 'none', color: t.accent, lineStyle: { width: 2 }, areaStyle: { color: t.accent, opacity: 0.08 } },
    ],
  });
}
