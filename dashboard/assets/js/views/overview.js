// Overview: how the sectors compare on performance, valuation, quality and risk.

import { createChart, base, valueAxis, categoryAxis, tooltip, tooltipHtml, tokens, divergingTokens, disposeCharts, placeLabels } from '../charts.js';
import { diverging, inkOn } from '../colors.js';
import { cap, date, esc, pct, tone, value } from '../format.js';
import { seg, onSeg, tile, legend, scaleLegend, metricSelect, onSelect } from '../components.js';
import { Dataset, VALUATION_ORDER, SIGNAL_ORDER, slugify } from '../store.js';
import { setParams, openStock } from '../router.js';
import { isNum, mean, quantile, returns, std } from '../stats.js';

export const title = () => 'Overview';

const MAP_METRICS = [
  '1w_return', '1m_return', '3m_return', 'ytd_return', '1y_return', 'excess_return',
  'valuation_score', 'forward_pe', 'quality_score', 'technical_score', 'price_vs_sma_200', 'analyst_upside',
];

export function render(root, ds, { params }) {
  const periods = ds.availablePeriods();
  let period = periods.some((p) => p.key === params.get('period')) ? params.get('period') : '1Y';
  if (!periods.some((p) => p.key === period)) period = periods[periods.length - 1]?.key;
  let weighting = params.get('w') === 'equal' ? 'equal' : 'cap';
  const mapMetrics = MAP_METRICS.filter((k) => ds.has(k));
  let mapMetric = mapMetrics.includes(params.get('color')) ? params.get('color') : mapMetrics.find((k) => k === '1y_return') || mapMetrics[0];

  const { analyzed, size } = ds.meta.universe;
  root.innerHTML = `
    <header class="page-head">
      <div>
        <h1>Sector overview</h1>
        <p class="lede">${analyzed} constituents of the ${esc(ds.meta.universe.name)} across ${ds.sectors.length} GICS sectors,
          compared on performance, valuation, quality, risk and momentum.</p>
      </div>
    </header>

    <div class="kpis">${kpis(ds)}</div>

    <section class="section">
      <div class="section-head">
        <h2>Sector performance</h2>
        <p>${ds.history
          ? 'Sector indices built from the constituents’ daily closes. Cap-weighted holds today’s share counts; equal-weighted gives every stock the same weight and shows breadth.'
          : 'Median return of the stocks in each sector.'}</p>
      </div>
      <div class="toolbar">
        ${seg('period', periods.map((p) => [p.key, p.key]), period, 'Period')}
        ${ds.history ? seg('w', [['cap', 'Cap-weighted'], ['equal', 'Equal-weighted']], weighting, 'Weighting') : ''}
      </div>
      <div class="grid">
        <div class="card ${ds.history ? 'span-5' : 'span-12'}">
          <div class="card-head"><h3>Return by sector</h3><span class="sub" data-perf-sub></span></div>
          <div class="chart" data-chart="ranking" style="height:430px"></div>
        </div>
        ${ds.history ? `
        <div class="card span-7">
          <div class="card-head"><h3>Path over the period</h3>
            <span class="aside">${legend([
              { color: 'var(--accent)', label: 'Sector', kind: 'line' },
              { color: 'var(--context)', label: 'S&P 500 (SPY)', kind: 'line' },
            ])}</span></div>
          <div class="multiples" data-multiples></div>
        </div>` : ''}
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>Sector scorecard</h2>
        <p>Median constituent per sector. Shading compares each sector with the other sectors:
          blue is favourable, red unfavourable for that metric; beta and size are left unshaded. Select a row to open the sector.</p>
      </div>
      <div class="card flush">
        <div class="table-wrap" data-scorecard></div>
        <div class="table-foot">${scaleLegend('Unfavourable', 'Favourable')}<span>Shading: distance from the cross-sector mean in standard deviations, capped at ±2.</span></div>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>Market map</h2>
        <p>Every stock sized by market cap and grouped by sector. Select a stock for its details.</p>
      </div>
      <div class="toolbar">
        <label class="field">Color by ${metricSelect(mapMetrics.map((k) => ds.metric(k)), { name: 'color', value: mapMetric, label: 'Color the map by' })}</label>
        <span class="spacer"></span>
        <span data-map-legend></span>
      </div>
      <div class="card"><div class="chart xl" data-chart="map" role="img" aria-label="Treemap of all stocks by market cap"></div></div>
    </section>

    <section class="section">
      <div class="grid">
        <div class="card span-6">
          <div class="card-head"><h3>Risk vs return</h3><span class="sub">${ds.history ? 'Sector indices, trailing year' : 'Median stock, trailing year'} · bubble area is market cap</span></div>
          <div class="chart tall" data-chart="risk"></div>
        </div>
        <div class="card span-6">
          <div class="card-head"><h3>Valuation mix</h3><span class="sub">Share of each sector’s stocks per valuation rating</span></div>
          ${legend(VALUATION_ORDER.map((label, i) => ({ color: `var(--ord-${i + 1})`, label })))}
          <div class="chart tall" data-chart="mix" style="margin-top:8px"></div>
        </div>
      </div>
    </section>`;

  const t = tokens();
  const drawPerformance = () => {
    disposeCharts(root.querySelector('[data-chart="ranking"]').parentElement);
    const multiples = root.querySelector('[data-multiples]');
    if (multiples) disposeCharts(multiples);
    renderRanking(root, ds, t, period, weighting);
    if (multiples) renderMultiples(multiples, ds, t, period, weighting);
  };
  drawPerformance();

  onSeg(root, 'period', (v) => {
    period = v;
    setParams({ period: v });
    drawPerformance();
  });
  onSeg(root, 'w', (v) => {
    weighting = v;
    setParams({ w: v === 'cap' ? null : v });
    drawPerformance();
  });

  renderScorecard(root.querySelector('[data-scorecard]'), ds, t);

  const mapChart = createChart(root.querySelector('[data-chart="map"]'));
  renderMap(mapChart, root, ds, t, mapMetric);
  onSelect(root, 'color', (v) => {
    mapMetric = v;
    setParams({ color: v });
    renderMap(mapChart, root, ds, t, mapMetric);
  });

  renderRisk(createChart(root.querySelector('[data-chart="risk"]')), ds, t);
  renderMix(createChart(root.querySelector('[data-chart="mix"]')), ds, t);
}

// ------------------------------------------------------------ KPIs

function kpis(ds) {
  const r1y = ds.metric('1y_return');
  const tiles = [];
  const { analyzed, size } = ds.meta.universe;
  tiles.push(tile('Stocks analysed', String(analyzed), `of ${size} constituents · ${ds.sectors.length} sectors`));

  const top = ds.sectors[0];
  tiles.push(tile('Total market cap', esc(cap(ds.totalCap)), `${esc(top)} ${pct(ds.sectorCap.get(top) / ds.totalCap, { digits: 0 })} of it`));

  const spy = ds.benchmarkReturn('1Y');
  const med1y = r1y ? ds.median('1y_return') : null;
  if (isNum(spy)) {
    tiles.push(tile('S&P 500, 1 year', `<span class="${tone(spy)}">${esc(pct(spy, { signed: true }))}</span>`,
      `Median stock ${esc(pct(med1y, { signed: true }))}`));
  } else if (r1y) {
    tiles.push(tile('Median 1-year return', `<span class="${tone(med1y)}">${esc(pct(med1y, { signed: true }))}</span>`, 'across all stocks'));
  }

  if (ds.has('forward_pe')) {
    const pe = ds.metric('forward_pe');
    const bySector = ds.sectors.map((s) => [s, ds.median('forward_pe', ds.peers(s))]).filter(([, v]) => isNum(v));
    const cheapest = bySector.sort((a, b) => a[1] - b[1])[0];
    tiles.push(tile('Median forward P/E', esc(value(pe, ds.median('forward_pe'))),
      cheapest ? `Cheapest: ${esc(cheapest[0])} ${esc(value(pe, cheapest[1]))}` : ''));
  }

  if (ds.has('price_vs_sma_200')) {
    const above = ds.stocks.filter((s) => isNum(s.price_vs_sma_200));
    const share = above.filter((s) => s.price_vs_sma_200 > 0).length / above.length;
    tiles.push(tile('Above 200-day average', esc(pct(share, { digits: 0 })), 'share of stocks in an uptrend'));
  }

  if (ds.has('technical_signal')) {
    const buy = ds.share('technical_signal', SIGNAL_ORDER.slice(0, 2));
    const sell = ds.share('technical_signal', SIGNAL_ORDER.slice(3));
    tiles.push(tile('Technical buy signals', esc(pct(buy, { digits: 0 })), `vs ${esc(pct(sell, { digits: 0 }))} sell signals`));
  } else if (ds.has('quality_score')) {
    tiles.push(tile('Median quality score', esc(value(ds.metric('quality_score'), ds.median('quality_score'))), 'on a 0–100 scale'));
  }
  return tiles.join('');
}

// ------------------------------------------------------------ performance

function rankedReturns(ds, period, weighting) {
  return ds.sectors
    .map((sector) => ({ sector, value: ds.sectorReturn(sector, period, weighting) }))
    .filter((d) => isNum(d.value))
    .sort((a, b) => b.value - a.value);
}

function renderRanking(root, ds, t, period, weighting) {
  const el = root.querySelector('[data-chart="ranking"]');
  const chart = createChart(el);
  const rows = rankedReturns(ds, period, weighting).reverse(); // bottom-up for the y axis
  const spy = ds.benchmarkReturn(period);
  const sub = root.querySelector('[data-perf-sub]');
  const end = ds.history ? ` to ${date(ds.history.dates.at(-1))}` : '';
  sub.textContent = ds.history
    ? `${weighting === 'cap' ? 'Cap-weighted' : 'Equal-weighted'} sector index · ${period}${end}`
    : `Median constituent · ${period}`;

  const label = (v) => pct(v, { signed: true });
  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 56, top: isNum(spy) ? 26 : 8, bottom: 8, containLabel: true },
    xAxis: valueAxis(t, { metric: { fmt: 'pct' }, splitNumber: 4 }),
    yAxis: categoryAxis(t, rows.map((r) => r.sector), { axisLine: { show: false } }),
    tooltip: tooltip(t, {
      trigger: 'item',
      formatter: (p) => tooltipHtml(p.name, [
        [null, `${period} return`, label(p.value)],
        ...(isNum(spy) ? [[null, 'vs S&P 500', label(p.value - spy)]] : []),
      ], 'Select to open the sector'),
    }),
    series: [{
      type: 'bar',
      barMaxWidth: 18,
      data: rows.map((r) => ({
        value: r.value,
        itemStyle: {
          color: r.value >= 0 ? t.pos : t.neg,
          borderRadius: r.value >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
        },
        label: { position: r.value >= 0 ? 'right' : 'left' },
      })),
      label: { show: true, color: t.ink2, fontSize: 11.5, formatter: (p) => label(p.value) },
      emphasis: { itemStyle: { opacity: 0.85 } },
      markLine: isNum(spy) ? {
        silent: true,
        symbol: 'none',
        lineStyle: { color: t.ink2, type: 'solid', width: 1 },
        label: { position: 'end', color: t.ink2, fontSize: 11, formatter: `S&P 500 ${label(spy)}` },
        data: [{ xAxis: spy }],
      } : undefined,
    }],
  });
  chart.on('click', (p) => { location.hash = `#/sector/${slugify(p.name)}`; });
}

function renderMultiples(el, ds, t, period, weighting) {
  const start = ds.periodStart(period);
  const dates = ds.history.dates.slice(start);
  const rebase = (series) => {
    const s = series.slice(start);
    const first = s.find(isNum);
    return s.map((v) => (isNum(v) && first ? v / first - 1 : null));
  };
  const spy = rebase(ds.benchmarkSeries());
  const ranked = rankedReturns(ds, period, weighting);
  const lines = ranked.map((r) => ({ ...r, path: rebase(ds.sectorSeries(r.sector, weighting)) }));

  // One shared scale so the panels compare honestly
  const all = lines.flatMap((l) => l.path).concat(spy).filter(isNum);
  const lo = Math.min(0, ...all);
  const hi = Math.max(0, ...all);
  const pad = (hi - lo) * 0.06;

  el.innerHTML = lines
    .map((l) => `<div class="multiple">
      <div class="multiple-head"><a href="#/sector/${slugify(l.sector)}">${esc(l.sector)}</a>
        <span class="num ${tone(l.value)}">${esc(pct(l.value, { signed: true }))}</span></div>
      <div class="chart" data-sector="${esc(l.sector)}"></div></div>`)
    .join('');

  for (const l of lines) {
    const chart = createChart(el.querySelector(`[data-sector="${CSS.escape(l.sector)}"]`));
    chart.setOption({
      ...base(t),
      animation: false,
      grid: { left: 0, right: 0, top: 6, bottom: 4 },
      xAxis: { type: 'category', data: dates, show: false, boundaryGap: false },
      yAxis: { type: 'value', min: lo - pad, max: hi + pad, show: false },
      tooltip: tooltip(t, {
        trigger: 'axis',
        axisPointer: { type: 'line', lineStyle: { color: t.axis, width: 1 } },
        formatter: (ps) => tooltipHtml(date(ps[0].axisValue), ps.map((p) => [p.color, p.seriesName, pct(p.value, { signed: true })])),
      }),
      series: [
        {
          name: 'S&P 500', type: 'line', data: spy, symbol: 'none', color: t.context,
          lineStyle: { width: 1.5 }, z: 1,
        },
        {
          name: l.sector, type: 'line', data: l.path, symbol: 'none', color: t.accent,
          lineStyle: { width: 2, cap: 'round', join: 'round' }, z: 2,
          markLine: { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: t.axis, width: 1, type: 'solid' }, data: [{ yAxis: 0 }] },
        },
      ],
    });
  }
}

// ------------------------------------------------------------ scorecard

const SCORECARD = [
  { key: 'count', label: 'Stocks', group: 'Size', description: 'Number of stocks analysed in the sector.' },
  { key: 'weight', label: 'Weight', group: 'Size', fmt: 'pct', description: 'Share of the total market cap.' },
  { key: '1m_return', group: 'Returns' },
  { key: '3m_return', group: 'Returns' },
  { key: '1y_return', group: 'Returns' },
  { key: 'forward_pe', group: 'Valuation' },
  { key: 'ev_to_ebitda', group: 'Valuation' },
  { key: 'fcf_yield', group: 'Valuation' },
  { key: 'undervalued', label: 'Undervalued', group: 'Valuation', better: 1, fmt: 'pct',
    description: 'Share of stocks rated undervalued or strongly undervalued.' },
  { key: 'roe', group: 'Quality' },
  { key: 'profit_margin', group: 'Quality' },
  { key: 'revenue_growth', group: 'Quality' },
  { key: 'debt_to_equity', group: 'Quality' },
  { key: 'volatility', group: 'Risk' },
  { key: 'max_drawdown', group: 'Risk' },
  { key: 'beta', group: 'Risk' },
  { key: 'breadth', label: 'Uptrend', group: 'Momentum', better: 1, fmt: 'pct',
    description: 'Share of stocks trading above their 200-day moving average.' },
  { key: 'buy_signals', label: 'Buy signals', group: 'Momentum', better: 1, fmt: 'pct',
    description: 'Share of stocks with a buy or strong buy technical signal.' },
];

function scorecardColumns(ds) {
  const requires = { undervalued: 'valuation_category', breadth: 'price_vs_sma_200', buy_signals: 'technical_signal' };
  return SCORECARD
    .filter((c) => ['count', 'weight'].includes(c.key) || ds.has(requires[c.key] || c.key))
    .map((c) => {
      const m = ds.metric(c.key);
      return {
        ...c,
        label: c.label || m.label,
        description: c.description || `Median ${m.label.toLowerCase()}. ${m.description}`,
        metric: m || { fmt: c.fmt || 'int', label: c.label },
        better: c.better ?? m?.better ?? 0,
      };
    });
}

function sectorStat(ds, sector, col) {
  const peers = ds.peers(sector);
  switch (col.key) {
    case 'count': return peers.length;
    case 'weight': return (sector ? ds.sectorCap.get(sector) : ds.totalCap) / ds.totalCap;
    case 'undervalued': return ds.share('valuation_category', VALUATION_ORDER.slice(0, 2), peers);
    case 'buy_signals': return ds.share('technical_signal', SIGNAL_ORDER.slice(0, 2), peers);
    case 'breadth': {
      const xs = peers.map((s) => s.price_vs_sma_200).filter(isNum);
      return xs.length ? xs.filter((x) => x > 0).length / xs.length : null;
    }
    default: return ds.median(col.key, peers);
  }
}

function renderScorecard(el, ds, t) {
  const columns = scorecardColumns(ds);
  const rows = ds.sectors.map((sector) => ({ sector, values: columns.map((c) => sectorStat(ds, sector, c)) }));
  const total = { sector: null, values: columns.map((c) => sectorStat(ds, null, c)) };
  const div = divergingTokens(t);

  // Shade by z-score across sectors, oriented so blue is favourable
  const shade = columns.map((c, j) => {
    if (!c.better || c.key === 'weight' || c.key === 'count') return null;
    const xs = rows.map((r) => r.values[j]);
    return { m: mean(xs), s: std(xs) };
  });

  let sort = { j: columns.findIndex((c) => c.key === 'weight'), dir: 'desc' };

  const draw = () => {
    const sorted = [...rows].sort((a, b) => {
      const va = a.values[sort.j];
      const vb = b.values[sort.j];
      if (!isNum(va) || !isNum(vb)) return isNum(va) ? -1 : isNum(vb) ? 1 : 0;
      return sort.dir === 'asc' ? va - vb : vb - va;
    });

    const groups = [];
    for (const c of columns) {
      if (groups.length && groups.at(-1).group === c.group) groups.at(-1).n += 1;
      else groups.push({ group: c.group, n: 1 });
    }

    const cellHtml = (c, j, v, shaded) => {
      const text = esc(c.key === 'count' ? String(v) : value(c.metric, v, { signed: c.metric.signed }));
      const sh = shade[j];
      if (!shaded || !sh || !isNum(v) || !sh.s) return `<td>${text}</td>`;
      const z = Math.max(-2, Math.min(2, ((v - sh.m) / sh.s) * c.better));
      const fill = diverging(z / 2.5, div);
      return `<td class="heat" style="--heat:${fill};--heat-ink:${inkOn(fill)}">${text}</td>`;
    };

    const head = columns
      .map((c, j) => `<th class="sortable" data-j="${j}" title="${esc(c.description)}"${sort.j === j
        ? ` aria-sort="${sort.dir === 'asc' ? 'ascending' : 'descending'}"` : ''}>${esc(c.label)}</th>`)
      .join('');

    el.innerHTML = `<table class="data scorecard">
      <thead>
        <tr class="group"><th class="sticky-col"></th>${groups.map((g) => `<th colspan="${g.n}">${esc(g.group)}</th>`).join('')}</tr>
        <tr><th class="sticky-col sortable" data-j="-1">Sector</th>${head}</tr>
      </thead>
      <tbody>
        ${sorted.map((r) => `<tr data-sector="${esc(r.sector)}" tabindex="0">
          <td class="sticky-col"><a class="sector-link" href="#/sector/${slugify(r.sector)}">${esc(r.sector)}</a></td>
          ${columns.map((c, j) => cellHtml(c, j, r.values[j], true)).join('')}</tr>`).join('')}
        <tr class="total" style="cursor:default"><td class="sticky-col"><strong>All stocks</strong></td>
          ${columns.map((c, j) => cellHtml(c, j, total.values[j], false)).join('')}</tr>
      </tbody></table>`;
  };

  el.addEventListener('click', (e) => {
    const th = e.target.closest('th[data-j]');
    if (th) {
      const j = Number(th.dataset.j);
      if (j < 0) return;
      sort = sort.j === j ? { j, dir: sort.dir === 'asc' ? 'desc' : 'asc' } : { j, dir: 'desc' };
      return draw();
    }
    const tr = e.target.closest('tr[data-sector]');
    if (tr && !e.target.closest('a')) location.hash = `#/sector/${slugify(tr.dataset.sector)}`;
  });
  el.addEventListener('keydown', (e) => {
    const tr = e.target.closest('tr[data-sector]');
    if (tr && e.key === 'Enter') location.hash = `#/sector/${slugify(tr.dataset.sector)}`;
  });
  draw();
}

// ------------------------------------------------------------ market map

/** Map a metric onto [-1, 1]: centred on 0 for signed metrics, else on the median; blue = favourable. */
function colorScale(ds, key) {
  const m = ds.metric(key);
  const xs = ds.values(key).filter(isNum);
  const center = m.signed && m.fmt !== 'ratio' ? 0 : key === 'valuation_score' ? 1 : quantile(xs, 0.5);
  const spread = quantile(xs.map((x) => Math.abs(x - center)), 0.9) || 1;
  const direction = m.better || 1;
  return { center, spread, at: (v) => (isNum(v) ? (direction * (v - center)) / spread : null) };
}

function renderMap(chart, root, ds, t, key) {
  const m = ds.metric(key);
  const scale = colorScale(ds, key);
  const div = divergingTokens(t);
  // The scale saturates at these values: unfavourable on the left, favourable on the right
  const worst = scale.center - scale.spread * (m.better || 1);
  const best = scale.center + scale.spread * (m.better || 1);
  root.querySelector('[data-map-legend]').innerHTML =
    scaleLegend(value(m, worst, { signed: m.signed }), value(m, best, { signed: m.signed }));

  // Tile area is proportional to market cap: label only tiles that can hold the text
  const pxPerCap = (chart.getWidth() * chart.getHeight() * 0.85) / ds.totalCap;
  const data = ds.sectors.map((sector) => ({
    name: sector,
    children: ds.peers(sector)
      .filter((s) => isNum(s.market_cap) && s.market_cap > 0)
      .map((s) => {
        const fill = diverging(scale.at(s[key]), div);
        const area = s.market_cap * pxPerCap;
        return {
          name: s.ticker,
          value: s.market_cap,
          stock: s,
          itemStyle: { color: fill },
          label: { show: area >= 2000, color: inkOn(fill), formatter: area >= 4200 ? undefined : '{t|{b}}' },
        };
      }),
  }));

  chart.setOption({
    ...base(t),
    tooltip: tooltip(t, {
      formatter: (p) => {
        const s = p.data?.stock;
        if (!s) return tooltipHtml(p.name, [[null, 'Market cap', cap(p.value)], [null, 'Weight', pct(p.value / ds.totalCap)]]);
        return tooltipHtml(`${s.ticker} · ${s.name}`, [
          [null, m.label, value(m, s[key], { signed: m.signed })],
          [null, 'Market cap', cap(s.market_cap)],
          [null, 'Sector', s.sector],
        ]);
      },
    }),
    series: [{
      type: 'treemap',
      data,
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      top: 0, left: 0, right: 0, bottom: 0,
      squareRatio: 0.5 * (1 + Math.sqrt(5)),
      label: {
        show: true,
        formatter: (p) => `{t|${p.name}}\n{v|${value(m, p.data.stock?.[key], { signed: m.signed, short: true })}}`,
        rich: { t: { fontSize: 12, fontWeight: 600, lineHeight: 15 }, v: { fontSize: 11, lineHeight: 14 } },
        overflow: 'truncate',
      },
      upperLabel: {
        show: true, height: 22, color: t.ink, fontSize: 12, fontWeight: 600,
        formatter: (p) => p.name,
      },
      levels: [
        { itemStyle: { color: t.surface, borderColor: t.surface, borderWidth: 0, gapWidth: 4 }, upperLabel: { show: false } },
        { itemStyle: { color: t.surface, borderColor: t.surface, borderWidth: 0, gapWidth: 2 } },
        { itemStyle: { borderColor: t.surface, borderWidth: 1, gapWidth: 0 } },
      ],
    }],
  }, true);

  chart.off('click');
  chart.on('click', (p) => {
    if (p.data?.stock) openStock(p.data.stock.ticker);
    else if (p.data?.children) location.hash = `#/sector/${slugify(p.name)}`;
  });
}

// ------------------------------------------------------------ risk vs return, valuation mix

function riskReturnPoints(ds) {
  if (ds.history) {
    const start = ds.periodStart('1Y');
    const annualVol = (series) => std(returns(series.slice(start))) * Math.sqrt(252);
    const points = ds.sectors.map((sector) => {
      const series = ds.sectorSeries(sector, 'cap');
      return { name: sector, vol: annualVol(series), ret: Dataset.seriesReturn(series, start), cap: ds.sectorCap.get(sector) };
    });
    const spy = ds.benchmarkSeries();
    return { points, benchmark: spy ? { name: 'S&P 500', vol: annualVol(spy), ret: Dataset.seriesReturn(spy, start) } : null };
  }
  return {
    points: ds.sectors.map((sector) => ({
      name: sector,
      vol: ds.median('volatility', ds.peers(sector)),
      ret: ds.median('1y_return', ds.peers(sector)),
      cap: ds.sectorCap.get(sector),
    })),
    benchmark: null,
  };
}

function renderRisk(chart, ds, t) {
  const { points, benchmark } = riskReturnPoints(ds);
  const valid = points.filter((p) => isNum(p.vol) && isNum(p.ret));
  const maxCap = Math.max(...valid.map((p) => p.cap));
  const size = (c) => 10 + 34 * Math.sqrt(c / maxCap);

  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 40, top: 30, bottom: 28, containLabel: true },
    xAxis: valueAxis(t, { metric: { fmt: 'pct' }, name: 'Volatility (annualised)', nameLocation: 'middle', nameGap: 28, scale: true }),
    yAxis: valueAxis(t, { metric: { fmt: 'pct' }, name: '1-year return', nameLocation: 'end', scale: true }),
    tooltip: tooltip(t, {
      trigger: 'item',
      formatter: (p) => tooltipHtml(p.data.name, [
        [null, '1-year return', pct(p.data.value[1], { signed: true })],
        [null, 'Volatility', pct(p.data.value[0])],
        [null, 'Return / volatility', (p.data.value[1] / p.data.value[0]).toFixed(2)],
        ...(p.data.cap ? [[null, 'Market cap', cap(p.data.cap)]] : []),
      ]),
    }),
    series: [
      {
        type: 'scatter',
        data: valid.map((p) => ({ name: p.name, value: [p.vol, p.ret], cap: p.cap, symbolSize: size(p.cap) })),
        itemStyle: { color: t.accent, opacity: 0.78, borderColor: t.surface, borderWidth: 2 },
        label: { show: true, color: t.ink2, fontSize: 11, formatter: (p) => p.data.name },
        emphasis: { scale: 1.08, itemStyle: { opacity: 1 } },
      },
      ...(benchmark && isNum(benchmark.vol) ? [{
        type: 'scatter',
        data: [{ name: benchmark.name, value: [benchmark.vol, benchmark.ret] }],
        symbol: 'diamond',
        symbolSize: 13,
        itemStyle: { color: t.ink2, borderColor: t.surface, borderWidth: 2 },
        label: { show: true, position: 'left', color: t.ink, fontSize: 11, fontWeight: 600, formatter: (p) => p.data.name },
      }] : []),
    ],
  });
  // Sectors are told apart by their labels, so every bubble keeps one
  placeLabels(chart, 0, { font: `11px ${t.font}` });
  chart.on('click', (p) => {
    if (p.data?.cap) location.hash = `#/sector/${slugify(p.data.name)}`;
  });
}

function renderMix(chart, ds, t) {
  const rows = ds.sectors
    .map((sector) => {
      const peers = ds.peers(sector).filter((s) => s.valuation_category);
      const shares = VALUATION_ORDER.map((label) => peers.filter((s) => s.valuation_category === label).length / (peers.length || 1));
      return { sector, shares, net: shares[0] + shares[1] - shares[3] - shares[4] };
    })
    .sort((a, b) => a.net - b.net); // most undervalued on top

  const [su, u, f, o, so] = [0, 1, 2, 3, 4];
  const segment = (name, idx, sign, half = false) => ({
    name,
    type: 'bar',
    stack: 'mix',
    barMaxWidth: 20,
    data: rows.map((r) => sign * r.shares[idx] * (half ? 0.5 : 1)),
    itemStyle: { color: t.ord[idx], borderColor: t.surface, borderWidth: 1 },
    label: {
      show: !half,
      color: inkOn(t.ord[idx]),
      fontSize: 10.5,
      formatter: (p) => (Math.abs(p.value) >= 0.12 ? pct(Math.abs(p.value), { digits: 0 }) : ''),
    },
    emphasis: { focus: 'none' },
  });

  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 16, top: 4, bottom: 8, containLabel: true },
    xAxis: valueAxis(t, { min: -1, max: 1, interval: 0.25, formatter: (v) => pct(Math.abs(v), { digits: 0 }) }),
    yAxis: categoryAxis(t, rows.map((r) => r.sector), { axisLine: { show: false } }),
    tooltip: tooltip(t, {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: t.surface2 } },
      formatter: (ps) => {
        const r = rows[ps[0].dataIndex];
        return tooltipHtml(r.sector, VALUATION_ORDER.map((label, i) => [t.ord[i], label, pct(r.shares[i], { digits: 0 })]));
      },
    }),
    series: [
      segment('Fairly Valued', f, -1, true),
      segment('Undervalued', u, -1),
      segment('Strongly Undervalued', su, -1),
      segment('Fairly Valued', f, 1, true),
      segment('Overvalued', o, 1),
      segment('Strongly Overvalued', so, 1),
    ],
  });
}
