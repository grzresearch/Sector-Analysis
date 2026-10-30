// Sector deep dive: one sector against the whole universe, down to every stock.

import { createChart, base, valueAxis, tooltip, tooltipHtml, tokens, nearestPointHover, disposeCharts } from '../charts.js';
import { cap, date, esc, pct, tone, value } from '../format.js';
import { seg, onSeg, tile, legend, StockTable, COLUMN_SETS, columnSet } from '../components.js';
import { slugify } from '../store.js';
import { setParams, openStock } from '../router.js';
import { isNum, median } from '../stats.js';

export const title = (ds, segments) => ds.sectorFromSlug(segments[1]) || 'Sectors';

const KPI_METRICS = ['forward_pe', 'ev_to_ebitda', 'roe', 'revenue_growth', 'volatility', 'quality_score'];

const PROFILE_METRICS = [
  'forward_pe', 'ev_to_ebitda', 'fcf_yield', 'dividend_yield',
  'roe', 'profit_margin', 'revenue_growth', 'debt_to_equity',
  '1y_return', '3m_return', 'volatility', 'sharpe_ratio',
  'quality_score', 'technical_score', 'analyst_upside',
];

export function render(root, ds, { segments, params }) {
  const sector = ds.sectorFromSlug(segments[1]);
  if (!sector) {
    location.replace(`#/sector/${slugify(ds.sectors[0])}`);
    return;
  }
  const stocks = ds.peers(sector);
  const periods = ds.history ? ds.availablePeriods() : [];
  let period = periods.some((p) => p.key === params.get('period')) ? params.get('period') : '1Y';
  let weighting = params.get('w') === 'equal' ? 'equal' : 'cap';
  let columns = COLUMN_SETS.some(([k]) => k === params.get('cols')) ? params.get('cols') : 'overview';

  const r1y = ds.sectorReturn(sector, '1Y');
  const share = ds.sectorCap.get(sector) / ds.totalCap;
  const picks = stocks.filter((s) => isNum(s.valuation_score)).sort((a, b) => a.valuation_score - b.valuation_score).slice(0, 6);

  root.innerHTML = `
    <nav class="pills" aria-label="Sectors">${ds.sectors
      .map((s) => `<a href="#/sector/${slugify(s)}"${s === sector ? ' aria-current="page"' : ''}>${esc(s)}</a>`)
      .join('')}</nav>

    <header class="page-head">
      <div>
        <h1>${esc(sector)}</h1>
        <p class="lede">${stocks.length} stocks · ${esc(cap(ds.sectorCap.get(sector)))} market cap,
          ${esc(pct(share, { digits: 1 }))} of the universe${isNum(r1y)
            ? ` · <span class="${tone(r1y)}">${esc(pct(r1y, { signed: true }))}</span> over the past year` : ''}</p>
      </div>
    </header>

    <div class="kpis">${KPI_METRICS.filter((k) => ds.has(k)).map((k) => kpi(ds, k, stocks)).join('')}</div>

    <section class="section">
      <div class="grid">
        <div class="card ${ds.history ? 'span-8' : 'span-12'}">
          ${ds.history ? `
          <div class="card-head"><h3>Sector index vs S&amp;P 500</h3>
            <span class="aside">${legend([
              { color: 'var(--accent)', label: sector, kind: 'line' },
              { color: 'var(--context)', label: 'S&P 500 (SPY)', kind: 'line' },
            ])}</span></div>
          <div class="toolbar">
            ${seg('period', periods.map((p) => [p.key, p.key]), period, 'Period')}
            ${seg('w', [['cap', 'Cap-weighted'], ['equal', 'Equal-weighted']], weighting, 'Weighting')}
          </div>
          <div class="chart" data-chart="index"></div>` : `
          <div class="card-head"><h3>Sector index</h3></div>
          <p class="note">Price history is not part of the demo data. Run the analysis with live data to see the sector index.</p>`}
        </div>
        <div class="card ${ds.history ? 'span-4' : 'span-12'}">
          <div class="card-head"><h3>Cheapest vs sector peers</h3><span class="sub">Lowest valuation score</span></div>
          <ol class="rank-list">${picks.map((s, i) => `
            <li data-ticker="${esc(s.ticker)}" tabindex="0">
              <span class="rank">${i + 1}</span>
              <span><span class="ticker">${esc(s.ticker)}</span><span class="name">${esc(s.name)}</span></span>
              <span class="value">${esc(value(ds.metric('forward_pe'), s.forward_pe))}<small>fwd P/E · score ${esc(value(ds.metric('valuation_score'), s.valuation_score))}</small></span>
            </li>`).join('')}</ol>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>Factor profile</h2>
        <p>Each dot is one of the sector’s stocks, placed by its percentile among all ${ds.stocks.length} stocks.
          Every row is oriented so that the right is favourable (a low P/E sits right), so clusters on the right are sector strengths.
          The dark tick marks the sector median.</p>
      </div>
      <div class="card"><div class="chart" data-chart="profile"></div></div>
    </section>

    <section class="section">
      <div class="section-head"><h2>Constituents</h2></div>
      <div class="toolbar">${seg('cols', COLUMN_SETS.map(([k, label]) => [k, label]), columns, 'Columns')}</div>
      <div class="card flush"><div class="table-wrap scroll-y" data-table></div></div>
    </section>`;

  const t = tokens();

  if (ds.history) {
    const indexEl = root.querySelector('[data-chart="index"]');
    const drawIndex = () => {
      disposeCharts(indexEl.parentElement);
      renderIndex(createChart(indexEl), ds, t, sector, period, weighting);
    };
    drawIndex();
    onSeg(root, 'period', (v) => { period = v; setParams({ period: v }); drawIndex(); });
    onSeg(root, 'w', (v) => { weighting = v; setParams({ w: v === 'cap' ? null : v }); drawIndex(); });
  }

  for (const li of root.querySelectorAll('.rank-list li')) {
    li.addEventListener('click', () => openStock(li.dataset.ticker));
    li.addEventListener('keydown', (e) => e.key === 'Enter' && openStock(li.dataset.ticker));
  }

  renderProfile(root.querySelector('[data-chart="profile"]'), ds, t, stocks);

  const table = new StockTable(root.querySelector('[data-table]'), ds, {
    columns: columnSet(ds, columns),
    sort: { key: 'market_cap', dir: 'desc' },
    onRowClick: openStock,
  });
  table.render(stocks);
  onSeg(root, 'cols', (v) => {
    columns = v;
    setParams({ cols: v === 'overview' ? null : v });
    table.columns = columnSet(ds, v);
    table.render(stocks);
  });
}

function kpi(ds, key, stocks) {
  const m = ds.metric(key);
  const here = ds.median(key, stocks);
  const all = ds.median(key);
  let verdict = '';
  if (isNum(here) && isNum(all) && m.better) {
    const edge = ((here - all) * m.better) / (Math.abs(all) || 1);
    verdict = Math.abs(edge) < 0.01
      ? ' · in line'
      : ` · <span class="${edge > 0 ? 'pos' : 'neg'}">${edge > 0 ? 'better' : 'worse'}</span>`;
  }
  return tile(`${m.label} · median`, esc(value(m, here, { signed: m.signed })),
    `All stocks ${esc(value(m, all, { signed: m.signed }))}${verdict}`);
}

function renderIndex(chart, ds, t, sector, period, weighting) {
  const start = ds.periodStart(period);
  const dates = ds.history.dates.slice(start);
  const rebase = (series) => {
    const s = series.slice(start);
    const first = s.find(isNum);
    return s.map((v) => (isNum(v) && first ? v / first - 1 : null));
  };
  const sectorPath = rebase(ds.sectorSeries(sector, weighting));
  const spyPath = rebase(ds.benchmarkSeries());
  const endLabel = (name) => ({
    show: true,
    formatter: (p) => (p.dataIndex === dates.length - 1 ? `${name} ${pct(p.value, { signed: true })}` : ''),
    position: 'right', color: t.ink2, fontSize: 11,
  });

  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 118, top: 12, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category', data: dates, boundaryGap: false,
      axisLine: { lineStyle: { color: t.axis } }, axisTick: { show: false },
      axisLabel: {
        color: t.muted, fontSize: 11, hideOverlap: true, alignMinLabel: 'left', alignMaxLabel: 'right',
        formatter: (d) => date(d, { year: period === '2Y' || period === '1Y' }),
      },
    },
    yAxis: valueAxis(t, { metric: { fmt: 'pct' }, scale: true }),
    tooltip: tooltip(t, {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: t.axis } },
      formatter: (ps) => tooltipHtml(date(ps[0].axisValue), ps.map((p) => [p.color, p.seriesName, pct(p.value, { signed: true })])),
    }),
    series: [
      { name: 'S&P 500', type: 'line', data: spyPath, symbol: 'none', color: t.context, lineStyle: { width: 1.5 },
        label: endLabel('S&P 500'), labelLayout: { moveOverlap: 'shiftY' } },
      { name: sector, type: 'line', data: sectorPath, symbol: 'none', color: t.accent, lineStyle: { width: 2 },
        label: endLabel('Sector'), labelLayout: { moveOverlap: 'shiftY' },
        areaStyle: { color: t.accent, opacity: 0.08 } },
    ],
  });
}

/** Deterministic jitter in [-0.5, 0.5) from a ticker, so dots never jump between renders. */
function jitter(ticker) {
  let h = 2166136261;
  for (const c of ticker) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  return ((h >>> 0) % 1000) / 1000 - 0.5;
}

function renderProfile(el, ds, t, stocks) {
  const metrics = PROFILE_METRICS.map((k) => ds.metric(k)).filter((m) => m && m.better);
  el.style.height = `${metrics.length * 38 + 56}px`;
  const chart = createChart(el);

  const points = [];
  metrics.forEach((m, row) => {
    for (const s of stocks) {
      const p = ds.favourability(s, m.key);
      if (isNum(p)) points.push({ value: [p, row + jitter(s.ticker + m.key) * 0.56], stock: s, metric: m, pctl: p });
    }
  });
  const medians = metrics.map((m, row) => {
    const p = median(stocks.map((s) => ds.favourability(s, m.key)));
    return { value: [p, row], metric: m, sectorMedian: ds.median(m.key, stocks), universeMedian: ds.median(m.key) };
  });

  chart.setOption({
    ...base(t),
    // containLabel does not measure customValues labels, so reserve their width
    grid: { left: 136, right: 16, top: 28, bottom: 8 },
    xAxis: valueAxis(t, {
      min: 0, max: 100, interval: 25, position: 'top',
      axisLabel: {
        color: t.muted, fontSize: 11,
        formatter: (v) => (v === 0 ? 'Less favourable' : v === 100 ? 'More favourable' : v === 50 ? 'All stocks median' : ''),
        alignMinLabel: 'left', alignMaxLabel: 'right',
      },
    }),
    yAxis: {
      // Ticks fall between rows (row separators); labels sit on the rows themselves
      type: 'value', min: -0.5, max: metrics.length - 0.5, inverse: true, interval: 1,
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } },
      axisLabel: {
        color: t.ink2, fontSize: 12,
        customValues: metrics.map((_, i) => i),
        formatter: (v) => metrics[v]?.label ?? '',
      },
    },
    tooltip: tooltip(t, {
      trigger: 'item',
      triggerOn: 'none',
      formatter: (p) => {
        const d = p.data;
        if (d.stock) {
          return tooltipHtml(`${d.stock.ticker} · ${d.stock.name}`, [
            [null, d.metric.label, value(d.metric, d.stock[d.metric.key], { signed: d.metric.signed })],
            [null, 'Percentile (favourable)', `${Math.round(d.pctl)}`],
          ]);
        }
        return tooltipHtml(d.metric.label, [
          [null, 'Sector median', value(d.metric, d.sectorMedian, { signed: d.metric.signed })],
          [null, 'All stocks median', value(d.metric, d.universeMedian, { signed: d.metric.signed })],
        ]);
      },
    }),
    series: [
      {
        type: 'scatter',
        data: points,
        symbolSize: 8,
        itemStyle: { color: t.accent, opacity: 0.6, borderColor: t.surface, borderWidth: 1 },
        emphasis: { scale: 1.6, itemStyle: { opacity: 1, borderWidth: 2 } },
      },
      {
        type: 'scatter',
        data: medians,
        symbol: 'rect',
        symbolSize: [3, 24],
        itemStyle: { color: t.ink },
        silent: true,
        z: 3,
      },
    ],
  });
  nearestPointHover(chart, 0, { radius: 18, onClick: (i) => openStock(points[i].stock.ticker) });
}
