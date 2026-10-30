// Screener: filter and rank every stock; the whole screen lives in the URL.

import { esc, value } from '../format.js';
import { seg, onSeg, metricSelect, StockTable, COLUMN_SETS, columnSet } from '../components.js';
import { VALUATION_ORDER, SIGNAL_ORDER, slugify } from '../store.js';
import { setParams, openStock } from '../router.js';
import { isNum } from '../stats.js';

export const title = () => 'Screener';

const VALUATION_FILTERS = [
  ['', 'Any valuation'],
  ['under', 'Undervalued'],
  ['fair', 'Fairly valued'],
  ['over', 'Overvalued'],
];
const VALUATION_GROUPS = { under: VALUATION_ORDER.slice(0, 2), fair: VALUATION_ORDER.slice(2, 3), over: VALUATION_ORDER.slice(3) };

const SIGNAL_FILTERS = [
  ['', 'Any signal'],
  ['buy', 'Buy signals'],
  ['neutral', 'Neutral'],
  ['sell', 'Sell signals'],
];
const SIGNAL_GROUPS = { buy: SIGNAL_ORDER.slice(0, 2), neutral: SIGNAL_ORDER.slice(2, 3), sell: SIGNAL_ORDER.slice(3) };

// Conditions are entered in display units: percent for fractions, $B for market cap
const FROM_INPUT = { pct: (x) => x / 100, cap: (x) => x * 1e9 };
const INPUT_UNIT = { pct: 'in %', pctpt: 'in %', multiple: 'multiple', cap: 'in $ billion' };

const parseConditions = (raw) =>
  (raw || '')
    .split(';')
    .map((part) => {
      const [key, op, v] = part.split(':');
      return { key, op, value: Number(v) };
    })
    .filter((c) => c.key && (c.op === 'ge' || c.op === 'le') && Number.isFinite(c.value));

const serializeConditions = (conditions) => conditions.map((c) => `${c.key}:${c.op}:${c.value}`).join(';');

export function render(root, ds, { params }) {
  const state = {
    q: params.get('q') || '',
    sector: ds.sectorFromSlug(params.get('sector')) || '',
    val: params.get('val') || '',
    sig: params.get('sig') || '',
    cols: COLUMN_SETS.some(([k]) => k === params.get('cols')) ? params.get('cols') : 'overview',
    conditions: parseConditions(params.get('f')).filter((c) => ds.has(c.key)),
  };
  const [sortKey, sortDir] = (params.get('sort') || 'market_cap:desc').split(':');
  const numeric = ds.numericMetrics();

  root.innerHTML = `
    <header class="page-head">
      <div>
        <h1>Screener</h1>
        <p class="lede">Filter and rank all ${ds.stocks.length} stocks on any metric. The screen is kept in the address bar, so it can be bookmarked and shared.</p>
      </div>
    </header>

    <div class="toolbar">
      <input class="input" data-q type="search" placeholder="Filter by ticker, company or industry" value="${esc(state.q)}" style="max-width:300px" aria-label="Filter by text">
      <select class="select" data-sector aria-label="Sector">
        <option value="">All sectors</option>
        ${ds.sectors.map((s) => `<option value="${esc(s)}"${s === state.sector ? ' selected' : ''}>${esc(s)}</option>`).join('')}
      </select>
      ${ds.has('valuation_category') ? `<select class="select" data-val aria-label="Valuation rating">${VALUATION_FILTERS
        .map(([v, l]) => `<option value="${v}"${v === state.val ? ' selected' : ''}>${l}</option>`).join('')}</select>` : ''}
      ${ds.has('technical_signal') ? `<select class="select" data-sig aria-label="Technical signal">${SIGNAL_FILTERS
        .map(([v, l]) => `<option value="${v}"${v === state.sig ? ' selected' : ''}>${l}</option>`).join('')}</select>` : ''}
    </div>

    <form class="toolbar" data-add autocomplete="off">
      <span data-chips style="display:contents"></span>
      ${metricSelect(numeric, { name: 'metric', value: 'forward_pe', label: 'Condition metric' })}
      <select class="select" data-op aria-label="Comparison"><option value="ge">at least</option><option value="le">at most</option></select>
      <input class="input" data-value type="number" step="any" required style="width:130px" aria-label="Threshold">
      <button class="button" type="submit">Add condition</button>
    </form>

    <div class="toolbar">
      ${seg('cols', COLUMN_SETS.map(([k, label]) => [k, label]), state.cols, 'Columns')}
      <span class="spacer"></span>
      <span class="muted" data-count></span>
      <button class="button" type="button" data-export>
        <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M8 2v8m0 0L5 7m3 3 3-3M3 13h10" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Export CSV</button>
    </div>

    <div class="card flush"><div class="table-wrap scroll-y" data-table style="max-height:72vh"></div></div>`;

  const $ = (sel) => root.querySelector(sel);
  const table = new StockTable($('[data-table]'), ds, {
    columns: columnSet(ds, state.cols),
    sort: { key: sortKey, dir: sortDir === 'asc' ? 'asc' : 'desc' },
    onSort: (s) => setParams({ sort: s.key === 'market_cap' && s.dir === 'desc' ? null : `${s.key}:${s.dir}` }),
    onRowClick: openStock,
    groupHeader: true,
    showSector: true,
  });

  const filtered = () => {
    const q = state.q.trim().toLowerCase();
    return ds.stocks.filter((s) =>
      (!q || [s.ticker, s.name, s.industry].some((f) => (f || '').toLowerCase().includes(q)))
      && (!state.sector || s.sector === state.sector)
      && (!state.val || VALUATION_GROUPS[state.val]?.includes(s.valuation_category))
      && (!state.sig || SIGNAL_GROUPS[state.sig]?.includes(s.technical_signal))
      && state.conditions.every((c) => {
        // A negative P/E is a loss, so it never passes a valuation threshold
        const v = ds.rankable(s, c.key);
        return isNum(v) && (c.op === 'ge' ? v >= c.value : v <= c.value);
      }));
  };

  const update = () => {
    const rows = filtered();
    table.render(rows);
    $('[data-count]').textContent = `${rows.length} of ${ds.stocks.length} stocks`;
    $('[data-chips]').innerHTML = state.conditions
      .map((c, i) => {
        const m = ds.metric(c.key);
        return `<span class="chip">${esc(m.label)} ${c.op === 'ge' ? '≥' : '≤'} ${esc(value(m, c.value))}
          <button type="button" data-remove="${i}" aria-label="Remove condition">×</button></span>`;
      })
      .join('');
    setParams({
      q: state.q || null,
      sector: state.sector ? slugify(state.sector) : null,
      val: state.val || null,
      sig: state.sig || null,
      f: serializeConditions(state.conditions) || null,
    });
  };

  $('[data-q]').addEventListener('input', (e) => { state.q = e.target.value; update(); });
  $('[data-sector]').addEventListener('change', (e) => { state.sector = e.target.value; update(); });
  $('[data-val]')?.addEventListener('change', (e) => { state.val = e.target.value; update(); });
  $('[data-sig]')?.addEventListener('change', (e) => { state.sig = e.target.value; update(); });
  onSeg(root, 'cols', (v) => {
    state.cols = v;
    setParams({ cols: v === 'overview' ? null : v });
    table.columns = columnSet(ds, v);
    update();
  });

  const metricInput = root.querySelector('[data-select="metric"]');
  const showUnit = () => { $('[data-value]').placeholder = `Value ${INPUT_UNIT[ds.metric(metricInput.value)?.fmt] || ''}`.trim(); };
  metricInput.addEventListener('change', showUnit);
  showUnit();

  $('[data-add]').addEventListener('submit', (e) => {
    e.preventDefault();
    const m = ds.metric(metricInput.value);
    const entered = Number($('[data-value]').value);
    if (!m || !Number.isFinite(entered)) return;
    state.conditions.push({ key: m.key, op: $('[data-op]').value, value: (FROM_INPUT[m.fmt] || Number)(entered) });
    $('[data-value]').value = '';
    update();
  });
  $('[data-chips]').addEventListener('click', (e) => {
    const button = e.target.closest('[data-remove]');
    if (!button) return;
    state.conditions.splice(Number(button.dataset.remove), 1);
    update();
  });

  // Export what the table shows, in its order
  $('[data-export]').addEventListener('click', () => downloadCsv(ds, table.sorted));
  update();
}

// CSV columns carry their unit in the header; fractions are written as percent
const CSV_UNITS = { pct: ' (%)', pctpt: ' (%)', cap: ' ($)', price: ' ($)', multiple: ' (x)' };

function csvValue(metric, v) {
  if (metric?.fmt === 'pct' && isNum(v)) return Number((v * 100).toPrecision(6));
  return v;
}

function downloadCsv(ds, rows) {
  const columns = ['ticker', 'name', 'sector', 'industry', ...ds.metrics.map((m) => m.key)];
  const header = ['Ticker', 'Name', 'Sector', 'Industry', ...ds.metrics.map((m) => m.label + (CSV_UNITS[m.fmt] || ''))];
  const quote = (v) => {
    if (v === null || v === undefined) return '';
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const csv = [header, ...rows.map((s) => columns.map((c) => csvValue(ds.metric(c), s[c])))]
    .map((r) => r.map(quote).join(','))
    .join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const a = Object.assign(document.createElement('a'), { href: url, download: `screen-${ds.meta.as_of}.csv` });
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
