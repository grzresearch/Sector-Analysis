// Factor Lab: relationships between metrics, distributions by sector, and
// how much the factor models actually explain.

import { createChart, base, valueAxis, categoryAxis, tooltip, tooltipHtml, tokens, divergingTokens, nearestPointHover, disposeCharts } from '../charts.js';
import { diverging, inkOn } from '../colors.js';
import { esc, number, pct, value } from '../format.js';
import { metricSelect, onSelect, scaleLegend, legend } from '../components.js';
import { slugify } from '../store.js';
import { setParams, openStock } from '../router.js';
import { box, isNum, linearFit, pearson, quantile, returns, spearman } from '../stats.js';

export const title = () => 'Factor Lab';

const pValue = (p) => (isNum(p) && p < 0.001 ? '< 0.001' : number(p, 3));

const CORRELATION_METRICS = [
  'forward_pe', 'price_to_book', 'ev_to_ebitda', 'fcf_yield', 'roe', 'profit_margin', 'revenue_growth',
  'debt_to_equity', '1y_return', 'volatility', 'beta', 'quality_score', 'valuation_score', 'technical_score',
];

export function render(root, ds, { params }) {
  const numeric = ds.numericMetrics();
  const pick = (key, fallback) => (ds.has(params.get(key)) ? params.get(key) : fallback);
  const state = {
    x: pick('x', ds.has('forward_pe') ? 'forward_pe' : numeric[0].key),
    y: pick('y', ds.has('1y_return') ? '1y_return' : numeric[1].key),
    dist: pick('dist', ds.has('forward_pe') ? 'forward_pe' : numeric[0].key),
    focus: ds.sectorFromSlug(params.get('focus')) || '',
    trim: params.get('trim') !== '0',
  };

  root.innerHTML = `
    <header class="page-head">
      <div>
        <h1>Factor Lab</h1>
        <p class="lede">How metrics relate across ${ds.stocks.length} stocks, how they spread within each sector,
          and how much of the cross-section of returns the factor models explain.</p>
      </div>
    </header>

    <div class="toolbar">
      <label class="field">Focus sector
        <select class="select" data-focus aria-label="Focus sector">
          <option value="">None (all stocks)</option>
          ${ds.sectors.map((s) => `<option value="${esc(s)}"${s === state.focus ? ' selected' : ''}>${esc(s)}</option>`).join('')}
        </select></label>
      <span class="muted" style="font-size:12.5px">Highlights the sector in the charts and computes the correlations within it.</span>
    </div>

    <section class="section" style="margin-top:20px">
      <div class="section-head"><h2>Scatter explorer</h2>
        <p>Pick any two metrics. The line is an ordinary least-squares fit; Spearman’s ρ measures monotonic association and is robust to outliers.</p></div>
      <div class="toolbar">
        <label class="field">X ${metricSelect(numeric, { name: 'x', value: state.x, label: 'X axis metric' })}</label>
        <label class="field">Y ${metricSelect(numeric, { name: 'y', value: state.y, label: 'Y axis metric' })}</label>
        <button class="button" type="button" data-swap title="Swap axes">⇄ Swap</button>
        <label class="check"><input type="checkbox" data-trim ${state.trim ? 'checked' : ''}> Trim to 1st–99th percentile</label>
      </div>
      <div class="grid">
        <div class="card span-8"><div class="chart tall" data-chart="scatter"></div></div>
        <div class="card span-4" data-scatter-stats></div>
      </div>
    </section>

    <section class="section">
      <div class="section-head"><h2>Distribution by sector</h2>
        <p>Box: middle 50% of stocks; whiskers reach the furthest stock within 1.5 interquartile ranges; dots are outliers. Sorted by median.</p></div>
      <div class="toolbar"><label class="field">Metric ${metricSelect(numeric, { name: 'dist', value: state.dist, label: 'Distribution metric' })}</label></div>
      <div class="card"><div class="chart tall" data-chart="box"></div></div>
    </section>

    <section class="section">
      <div class="section-head"><h2>Correlations</h2>
        <p>Rank correlation between metrics across stocks${ds.history ? ', and correlation of the sector indices’ daily returns over the past year' : ''}.</p></div>
      <div class="grid">
        <div class="card ${ds.history ? 'span-6' : 'span-12'}">
          <div class="card-head"><h3>Metric correlation</h3><span class="sub" data-corr-sub></span></div>
          <div class="chart tall" data-chart="corr"></div>
          ${scaleLegend('−1 (opposite)', '+1 (together)')}
        </div>
        ${ds.history ? `<div class="card span-6">
          <div class="card-head"><h3>Sector return correlation</h3><span class="sub">Daily returns of the cap-weighted indices, 1 year</span></div>
          <div class="chart tall" data-chart="sector-corr"></div>
          ${scaleLegend('−1', '+1')}
        </div>` : ''}
      </div>
    </section>

    <section class="section" data-models></section>`;

  const t = tokens();
  const $ = (sel) => root.querySelector(sel);

  const scatterEl = $('[data-chart="scatter"]');
  const drawScatter = () => {
    disposeCharts(scatterEl.parentElement);
    renderScatter(createChart(scatterEl), $('[data-scatter-stats]'), ds, t, state);
  };
  const boxEl = $('[data-chart="box"]');
  const drawBox = () => {
    disposeCharts(boxEl.parentElement);
    renderBoxes(createChart(boxEl), ds, t, state);
  };
  const corrEl = $('[data-chart="corr"]');
  const drawCorr = () => {
    disposeCharts(corrEl.parentElement);
    renderCorrelation(createChart(corrEl), $('[data-corr-sub]'), ds, t, state.focus);
  };

  drawScatter();
  drawBox();
  drawCorr();
  if (ds.history) renderSectorCorrelation(createChart($('[data-chart="sector-corr"]')), ds, t);
  renderModels($('[data-models]'), ds, t);

  onSelect(root, 'x', (v) => { state.x = v; setParams({ x: v }); drawScatter(); });
  onSelect(root, 'y', (v) => { state.y = v; setParams({ y: v }); drawScatter(); });
  onSelect(root, 'dist', (v) => { state.dist = v; setParams({ dist: v }); drawBox(); });
  $('[data-swap]').addEventListener('click', () => {
    [state.x, state.y] = [state.y, state.x];
    root.querySelector('[data-select="x"]').value = state.x;
    root.querySelector('[data-select="y"]').value = state.y;
    setParams({ x: state.x, y: state.y });
    drawScatter();
  });
  $('[data-trim]').addEventListener('change', (e) => {
    state.trim = e.target.checked;
    setParams({ trim: state.trim ? null : '0' });
    drawScatter();
  });
  $('[data-focus]').addEventListener('change', (e) => {
    state.focus = e.target.value;
    setParams({ focus: state.focus ? slugify(state.focus) : null });
    drawScatter();
    drawBox();
    drawCorr();
  });
}

// ------------------------------------------------------------ scatter

function renderScatter(chart, statsEl, ds, t, state) {
  const mx = ds.metric(state.x);
  const my = ds.metric(state.y);
  let stocks = ds.stocks.filter((s) => isNum(s[state.x]) && isNum(s[state.y]));
  const total = stocks.length;
  if (state.trim) {
    const bounds = (k) => [quantile(stocks.map((s) => s[k]), 0.01), quantile(stocks.map((s) => s[k]), 0.99)];
    const [x0, x1] = bounds(state.x);
    const [y0, y1] = bounds(state.y);
    stocks = stocks.filter((s) => s[state.x] >= x0 && s[state.x] <= x1 && s[state.y] >= y0 && s[state.y] <= y1);
  }
  const focus = state.focus;
  const inFocus = (s) => !focus || s.sector === focus;
  // Context first, focus on top
  const ordered = [...stocks.filter((s) => !inFocus(s)), ...stocks.filter(inFocus)];
  const subject = stocks.filter(inFocus);

  const xs = subject.map((s) => s[state.x]);
  const ys = subject.map((s) => s[state.y]);
  const fit = linearFit(xs, ys);
  const r = pearson(xs, ys);
  const rho = spearman(xs, ys);

  const xMin = Math.min(...stocks.map((s) => s[state.x]));
  const xMax = Math.max(...stocks.map((s) => s[state.x]));

  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 20, top: 24, bottom: 30, containLabel: true },
    xAxis: valueAxis(t, { metric: mx, name: mx.label, nameLocation: 'middle', nameGap: 30, scale: true }),
    yAxis: valueAxis(t, { metric: my, name: my.label, nameLocation: 'end', scale: true }),
    tooltip: tooltip(t, {
      trigger: 'item',
      triggerOn: 'none',
      formatter: (p) => {
        const s = p.data.stock;
        if (!s) return '';
        return tooltipHtml(`${s.ticker} · ${s.name}`, [
          [null, mx.label, value(mx, s[state.x], { signed: mx.signed })],
          [null, my.label, value(my, s[state.y], { signed: my.signed })],
          [null, 'Sector', s.sector],
        ]);
      },
    }),
    series: [
      {
        type: 'scatter',
        data: ordered.map((s) => ({
          value: [s[state.x], s[state.y]],
          stock: s,
          itemStyle: inFocus(s) ? { color: t.accent, opacity: focus ? 0.9 : 0.6 } : { color: t.context, opacity: 0.55 },
        })),
        symbolSize: 8,
        itemStyle: { borderColor: t.surface, borderWidth: 1 },
        emphasis: { scale: 1.5, itemStyle: { opacity: 1, borderWidth: 2 } },
      },
      ...(fit ? [{
        type: 'line',
        data: [[xMin, fit.intercept + fit.slope * xMin], [xMax, fit.intercept + fit.slope * xMax]],
        symbol: 'none',
        silent: true,
        lineStyle: { color: t.ink2, width: 1.5 },
        z: 3,
      }] : []),
    ],
  });
  nearestPointHover(chart, 0, { onClick: (i) => openStock(ordered[i].stock.ticker) });

  const strength = (x) => {
    if (!isNum(x)) return '';
    const a = Math.abs(x);
    return a < 0.1 ? 'none' : a < 0.3 ? 'weak' : a < 0.5 ? 'moderate' : 'strong';
  };
  statsEl.innerHTML = `
    <div class="card-head"><h3>${focus ? esc(focus) : 'All stocks'}</h3>
      <span class="sub">${subject.length} stocks${state.trim && total > stocks.length ? ` · ${total - stocks.length} trimmed` : ''}</span></div>
    ${focus ? legend([{ color: 'var(--accent)', label: focus }, { color: 'var(--context)', label: 'Other sectors' }]) : ''}
    <dl class="stat-row" style="margin-top:14px">
      <div><dt>Spearman ρ</dt><dd>${esc(number(rho, 2, { signed: true }))}</dd></div>
      <div><dt>Pearson r</dt><dd>${esc(number(r, 2, { signed: true }))}</dd></div>
      <div><dt>R²</dt><dd>${esc(fit ? pct(fit.r2) : '—')}</dd></div>
    </dl>
    <p class="muted" style="font-size:13px">
      ${isNum(rho) ? (strength(rho) === 'none'
        ? 'No meaningful rank association.'
        : `A <strong style="color:var(--ink)">${strength(rho)}</strong> ${rho >= 0 ? 'positive' : 'negative'} rank association.`) : ''}
      ${fit ? `Each additional ${esc(value(mx, unitStep(mx)))} of ${esc(mx.label)} goes with
        ${esc(value(my, fit.slope * unitStep(mx), { signed: true }))} of ${esc(my.label)} on average.` : ''}
      Association across stocks, not causation.</p>`;
}

/** A natural step of a metric for describing a slope ("per 1 point of P/E"). */
function unitStep(m) {
  return m.fmt === 'pct' ? 0.01 : m.fmt === 'cap' ? 1e9 : m.fmt === 'pctpt' ? 1 : m.fmt === 'num' || m.fmt === 'int' || m.fmt === 'multiple' ? 1 : 0.1;
}

// ------------------------------------------------------------ box plots

function renderBoxes(chart, ds, t, state) {
  const m = ds.metric(state.dist);
  const rows = ds.sectors
    .map((sector) => ({ sector, stats: box(ds.values(state.dist, ds.peers(sector))) }))
    .filter((r) => r.stats)
    .sort((a, b) => a.stats.median - b.stats.median);
  const all = ds.values(state.dist).filter(isNum);
  const lo = quantile(all, 0.01);
  const hi = quantile(all, 0.99);
  const universeMedian = quantile(all, 0.5);
  const isFocus = (r) => r.sector === state.focus;

  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 24, top: 24, bottom: 8, containLabel: true },
    xAxis: valueAxis(t, { metric: m, scale: true }),
    yAxis: categoryAxis(t, rows.map((r) => r.sector), {
      axisLine: { show: false },
      axisLabel: {
        color: t.ink2, fontSize: 12,
        formatter: (v) => (v === state.focus ? `{focus|${v}}` : v),
        rich: { focus: { color: t.ink, fontWeight: 600, fontSize: 12 } },
      },
    }),
    tooltip: tooltip(t, {
      trigger: 'item',
      formatter: (p) => {
        if (p.seriesType === 'scatter') return tooltipHtml(p.data.stock ? `${p.data.stock.ticker} · ${p.data.stock.name}` : '', [[null, m.label, value(m, p.data.value[0])]], 'Outlier');
        const r = rows[p.dataIndex];
        return tooltipHtml(r.sector, [
          [null, 'Median', value(m, r.stats.median)],
          [null, 'Middle 50%', `${value(m, r.stats.q1)} – ${value(m, r.stats.q3)}`],
          [null, 'Whiskers', `${value(m, r.stats.low)} – ${value(m, r.stats.high)}`],
          [null, 'Stocks', String(r.stats.n)],
        ]);
      },
    }),
    series: [
      {
        type: 'boxplot',
        layout: 'horizontal',
        boxWidth: [8, 18],
        data: rows.map((r) => ({
          value: [r.stats.low, r.stats.q1, r.stats.median, r.stats.q3, r.stats.high],
          itemStyle: {
            color: isFocus(r) ? t.accent : `${t.accent}22`,
            borderColor: isFocus(r) || !state.focus ? t.accent : t.context,
            borderWidth: 1.5,
          },
        })),
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: t.ink2, width: 1, type: 'solid' },
          label: { position: 'end', color: t.ink2, fontSize: 11, formatter: `All stocks ${value(m, universeMedian)}` },
          data: [{ xAxis: universeMedian }],
        },
      },
      {
        type: 'scatter',
        symbolSize: 6,
        itemStyle: { color: t.context, borderColor: t.surface, borderWidth: 1 },
        data: rows.flatMap((r, i) => ds.peers(r.sector)
          .filter((s) => r.stats.outliers.includes(s[state.dist]) && s[state.dist] >= lo && s[state.dist] <= hi)
          .map((s) => ({ value: [s[state.dist], i], stock: s }))),
      },
    ],
  });
  chart.on('click', (p) => {
    if (p.data?.stock) openStock(p.data.stock.ticker);
  });
}

// ------------------------------------------------------------ correlation heatmaps

function heatmap(chart, t, labels, matrix, { onCell = null, labelAbove = 0.5 } = {}) {
  const div = divergingTokens(t);
  const n = labels.length;
  const data = [];
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j < n; j += 1) {
      const v = matrix[i][j];
      const fill = i === j ? t.surface3 : diverging(isNum(v) ? v : null, div);
      data.push({
        value: [j, i, v],
        itemStyle: { color: fill },
        label: { show: i !== j && isNum(v) && Math.abs(v) >= labelAbove, color: inkOn(fill) },
      });
    }
  }
  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 8, top: 8, bottom: 8, containLabel: true },
    xAxis: categoryAxis(t, labels, { axisLine: { show: false }, axisLabel: { color: t.ink2, fontSize: 11, rotate: 45, interval: 0 }, splitArea: { show: false } }),
    yAxis: categoryAxis(t, labels, { axisLine: { show: false }, inverse: true, axisLabel: { color: t.ink2, fontSize: 11, interval: 0 } }),
    tooltip: tooltip(t, {
      trigger: 'item',
      formatter: (p) => tooltipHtml(`${labels[p.data.value[1]]} × ${labels[p.data.value[0]]}`, [
        [null, 'Correlation', number(p.data.value[2], 2, { signed: true })],
      ]),
    }),
    series: [{
      type: 'heatmap',
      data,
      itemStyle: { borderColor: t.surface, borderWidth: 2, borderRadius: 3 },
      label: { fontSize: 10, formatter: (p) => number(p.data.value[2], 2).replace(/^(−)?0\./, '$1.') },
      emphasis: { itemStyle: { borderColor: t.ink, borderWidth: 1 } },
    }],
  });
  if (onCell) chart.on('click', (p) => onCell(p.data.value[1], p.data.value[0]));
}

function renderCorrelation(chart, subEl, ds, t, focus) {
  const metrics = CORRELATION_METRICS.map((k) => ds.metric(k)).filter(Boolean);
  const stocks = ds.peers(focus || null);
  const matrix = metrics.map((a) => metrics.map((b) => (a === b ? 1 : spearman(ds.values(a.key, stocks), ds.values(b.key, stocks)))));
  subEl.textContent = `Spearman ρ · ${focus || 'all stocks'} (${stocks.length}) · select a cell to plot it`;
  heatmap(chart, t, metrics.map((m) => m.label), matrix, {
    onCell: (i, j) => {
      if (i !== j) location.hash = `#/lab?x=${metrics[j].key}&y=${metrics[i].key}${focus ? `&focus=${slugify(focus)}` : ''}`;
    },
  });
}

function renderSectorCorrelation(chart, ds, t) {
  const start = ds.periodStart('1Y');
  const series = ds.sectors.map((s) => returns(ds.sectorSeries(s, 'cap').slice(start)));
  const matrix = series.map((a) => series.map((b) => pearson(a, b)));
  heatmap(chart, t, ds.sectors, matrix, { labelAbove: 0 });
}

// ------------------------------------------------------------ models

function forestPlot(chart, ds, t, ols) {
  const rows = [...ols.coefficients].sort((a, b) => a.effect - b.effect);
  const labelOf = (term) => ds.metric(term)?.label || term;
  const significant = (c) => c.p < 0.05;
  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 24, top: 8, bottom: 28, containLabel: true },
    xAxis: valueAxis(t, { metric: { fmt: 'pct' }, name: 'Effect of +1 standard deviation on 1-year excess return', nameLocation: 'middle', nameGap: 28 }),
    yAxis: categoryAxis(t, rows.map((c) => labelOf(c.term)), { axisLine: { show: false } }),
    tooltip: tooltip(t, {
      trigger: 'item',
      formatter: (p) => {
        const c = rows[p.dataIndex];
        return tooltipHtml(labelOf(c.term), [
          [null, 'Effect (1 SD)', pct(c.effect, { signed: true, digits: 2 })],
          [null, '95% interval', `${pct(c.effect_ci[0], { signed: true, digits: 2 })} to ${pct(c.effect_ci[1], { signed: true, digits: 2 })}`],
          [null, 'p-value', pValue(c.p)],
        ], significant(c) ? 'Significant at the 5% level' : 'Not significant at the 5% level');
      },
    }),
    series: [
      {
        type: 'custom',
        renderItem: (params, api) => {
          const lo = api.coord([api.value(0), api.value(2)]);
          const hi = api.coord([api.value(1), api.value(2)]);
          const color = rows[params.dataIndex].p < 0.05 ? t.accent : t.context;
          const cap = 5;
          return {
            type: 'group',
            children: [
              { type: 'line', shape: { x1: lo[0], y1: lo[1], x2: hi[0], y2: hi[1] }, style: { stroke: color, lineWidth: 2 } },
              { type: 'line', shape: { x1: lo[0], y1: lo[1] - cap, x2: lo[0], y2: lo[1] + cap }, style: { stroke: color, lineWidth: 1.5 } },
              { type: 'line', shape: { x1: hi[0], y1: hi[1] - cap, x2: hi[0], y2: hi[1] + cap }, style: { stroke: color, lineWidth: 1.5 } },
            ],
          };
        },
        encode: { x: [0, 1], y: 2 },
        data: rows.map((c, i) => [c.effect_ci[0], c.effect_ci[1], i]),
        z: 1,
      },
      {
        type: 'scatter',
        symbolSize: 10,
        data: rows.map((c, i) => ({ value: [c.effect, i], itemStyle: { color: significant(c) ? t.accent : t.context } })),
        itemStyle: { borderColor: t.surface, borderWidth: 2 },
        markLine: { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: t.ink2, width: 1, type: 'solid' }, data: [{ xAxis: 0 }] },
        z: 2,
      },
    ],
  });
}

function importanceBars(chart, ds, t, ml) {
  const rows = [...ml.importance].reverse();
  chart.setOption({
    ...base(t),
    grid: { left: 8, right: 48, top: 4, bottom: 8, containLabel: true },
    xAxis: valueAxis(t, { metric: { fmt: 'pct' }, splitNumber: 3 }),
    yAxis: categoryAxis(t, rows.map((r) => ds.metric(r.feature)?.label || r.feature), { axisLine: { show: false } }),
    tooltip: tooltip(t, { trigger: 'item', formatter: (p) => tooltipHtml(p.name, [[null, 'Share of importance', pct(p.value)]]) }),
    series: [{
      type: 'bar',
      barMaxWidth: 16,
      data: rows.map((r) => r.share),
      itemStyle: { color: t.accent, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', color: t.ink2, fontSize: 11, formatter: (p) => pct(p.value, { digits: 0 }) },
    }],
  });
}

function renderModels(el, ds, t) {
  const { ols, ml, sectors = [] } = ds.models;
  if (!ols && !ml) {
    el.remove();
    return;
  }
  const sig = ols ? ols.coefficients.filter((c) => c.p < 0.05) : [];
  const labelOf = (term) => ds.metric(term)?.label || term;
  const best = ml?.models?.[0];
  const olsText = ols
    ? `Eight fundamental and risk factors explain <strong style="color:var(--ink)">${esc(pct(ols.r2))}</strong> of the variation in 1-year excess returns
       across ${ols.n} stocks (F-test p ${esc(pValue(ols.f_pvalue).startsWith('<') ? pValue(ols.f_pvalue) : `= ${pValue(ols.f_pvalue)}`)}). ${sig.length
         ? `Significant at the 5% level: ${sig.map((c) => esc(labelOf(c.term))).join(', ')}.`
         : 'No factor is significant at the 5% level.'}`
    : '';
  const mlText = best
    ? best.r2 < 0
      ? `Out of sample, every model scores below zero (best: ${esc(best.name)}, R² ${esc(number(best.r2, 2))}), so none beats simply forecasting the average return. The ratings on this site describe stocks; they are not return forecasts.`
      : `On stocks held out of training, the best model (${esc(best.name)}) explains ${esc(pct(best.r2))} of the variation in 1-year returns.
         The inputs, volatility in particular, are measured over the same period as the returns, so this explains the cross-section; it is not a forecast of future returns.`
    : '';

  el.innerHTML = `
    <div class="section-head"><h2>Factor models</h2>
      <p>Cross-sectional regressions from the analysis pipeline: which stock characteristics line up with returns, and whether any of it predicts.</p></div>
    <div class="grid">
      ${ols ? `<div class="card span-7">
        <div class="card-head"><h3>OLS: drivers of 1-year excess return</h3><span class="sub">Standardised effects with 95% confidence intervals</span></div>
        <dl class="stat-row">
          <div><dt>R²</dt><dd>${esc(pct(ols.r2))}</dd></div>
          <div><dt>Adjusted R²</dt><dd>${esc(pct(ols.adj_r2))}</dd></div>
          <div><dt>F-test p</dt><dd>${esc(pValue(ols.f_pvalue))}</dd></div>
          <div><dt>Stocks</dt><dd>${ols.n}</dd></div>
        </dl>
        ${legend([{ color: 'var(--accent)', label: 'Significant (p < 0.05)' }, { color: 'var(--context)', label: 'Not significant' }])}
        <div class="chart" data-chart="forest" style="height:340px;margin-top:8px"></div>
        <p class="muted" style="font-size:13px;margin-top:8px">${olsText}</p>
      </div>` : ''}
      ${ml ? `<div class="card span-5">
        <div class="card-head"><h3>Machine learning: 1-year return</h3><span class="sub">20% hold-out test set, 5-fold cross-validation</span></div>
        <div class="table-wrap"><table class="data">
          <thead><tr><th>Model</th><th>Test R²</th><th>RMSE</th><th>CV R²</th></tr></thead>
          <tbody>${ml.models.map((r) => `<tr style="cursor:default"><td>${esc(r.name)}</td>
            <td class="${r.r2 < 0 ? 'neg' : 'pos'}">${esc(number(r.r2, 3, { signed: true }))}</td>
            <td>${esc(pct(r.rmse))}</td>
            <td>${esc(number(r.cv_r2, 3, { signed: true }))} <span class="muted">± ${esc(number(r.cv_r2_std, 2))}</span></td></tr>`).join('')}</tbody>
        </table></div>
        <p class="muted" style="font-size:13px;margin:12px 0 16px">${mlText}</p>
        <h3 style="font-size:13px;margin-bottom:4px">Feature importance</h3>
        <p class="muted" style="font-size:12.5px">Average share across the five models</p>
        <div class="chart" data-chart="importance" style="height:240px"></div>
      </div>` : ''}
      ${sectors.length ? `<div class="card span-12 flush">
        <div class="card-head"><h3>Per-sector OLS: drivers of 1-year return</h3><span class="sub">Same eight factors, fitted within each sector of at least 20 stocks</span></div>
        <div class="table-wrap"><table class="data">
          <thead><tr><th>Sector</th><th>Stocks</th><th>R²</th><th>Adjusted R²</th><th class="left">Significant factors (p < 0.05)</th></tr></thead>
          <tbody>${sectors.map((s) => `<tr style="cursor:default"><td>${esc(s.sector)}</td><td>${s.n}</td><td>${esc(pct(s.r2))}</td>
            <td>${esc(pct(s.adj_r2))}</td><td class="left">${s.factors.length ? s.factors.map((f) => esc(labelOf(f))).join(', ') : '<span class="muted">none</span>'}</td></tr>`).join('')}</tbody>
        </table></div></div>` : ''}
    </div>`;

  if (ols) forestPlot(createChart(el.querySelector('[data-chart="forest"]')), ds, t, ols);
  if (ml) importanceBars(createChart(el.querySelector('[data-chart="importance"]')), ds, t, ml);
}
