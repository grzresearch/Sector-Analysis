// Shared UI pieces rendered as HTML strings, plus the sortable data table.

import { esc, tone, value } from './format.js';
import { LABEL_ORDERS, ZONE_STATUS } from './store.js';
import { isNum } from './stats.js';

// ------------------------------------------------------------ controls

/** Segmented control; `options` is a list of [value, label]. */
export function seg(name, options, active, label = name) {
  const buttons = options
    .map(([v, text]) => `<button type="button" data-value="${esc(v)}" aria-pressed="${String(v) === String(active)}">${esc(text)}</button>`)
    .join('');
  return `<div class="seg" role="group" aria-label="${esc(label)}" data-seg="${esc(name)}">${buttons}</div>`;
}

/** Call `fn(value)` when a button of the named segmented control is pressed. */
export function onSeg(root, name, fn) {
  root.querySelector(`[data-seg="${name}"]`)?.addEventListener('click', (e) => {
    const button = e.target.closest('button[data-value]');
    if (!button) return;
    for (const b of button.parentElement.children) b.setAttribute('aria-pressed', String(b === button));
    fn(button.dataset.value);
  });
}

/** <select> of metrics grouped by catalog group. */
export function metricSelect(metrics, { name, value: selected, label, none = null }) {
  const groups = new Map();
  for (const m of metrics) {
    if (!groups.has(m.group)) groups.set(m.group, []);
    groups.get(m.group).push(m);
  }
  const options = [...groups]
    .map(([group, ms]) => `<optgroup label="${esc(group)}">${ms
      .map((m) => `<option value="${esc(m.key)}"${m.key === selected ? ' selected' : ''}>${esc(m.label)}</option>`)
      .join('')}</optgroup>`)
    .join('');
  const empty = none ? `<option value=""${!selected ? ' selected' : ''}>${esc(none)}</option>` : '';
  return `<select class="select" data-select="${esc(name)}" aria-label="${esc(label)}">${empty}${options}</select>`;
}

export function onSelect(root, name, fn) {
  root.querySelector(`[data-select="${name}"]`)?.addEventListener('change', (e) => fn(e.target.value));
}

// ------------------------------------------------------------ figures

export function tile(label, valueHtml, foot = '') {
  return `<div class="tile"><div class="tile-label">${esc(label)}</div>
    <div class="tile-value">${valueHtml}</div>${foot ? `<div class="tile-foot">${foot}</div>` : ''}</div>`;
}

const STATUS_ICONS = {
  good: '<path d="M4 8.5 7 11l5-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  warning: '<path d="M8 4.5v4M8 11.2v.1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  critical: '<path d="m5 5 6 6M11 5l-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
};

function statusIcon(status) {
  return `<svg class="status-icon" viewBox="0 0 16 16" style="color:var(--${status === 'good' ? 'good' : status === 'warning' ? 'warning' : 'critical'})" aria-hidden="true">
    <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.4"/>${STATUS_ICONS[status]}</svg>`;
}

/** Ordinal swatch color (1 = most favourable ... 5) for a categorical label. */
function labelRank(key, label) {
  const order = LABEL_ORDERS[key];
  const i = order ? order.indexOf(label) : -1;
  return i >= 0 ? i + 1 : null;
}

/** A categorical value as a tag: ordinal swatch, or status icon for Z-score zones. */
export function labelTag(key, label, { prefix = '' } = {}) {
  if (!label) return '<span class="muted">—</span>';
  const text = esc(prefix ? `${prefix}: ${label}` : label);
  if (key === 'z_score_zone' && ZONE_STATUS[label]) return `<span class="tag">${statusIcon(ZONE_STATUS[label])}${text}</span>`;
  const rank = labelRank(key, label);
  const swatch = rank ? `<span class="swatch" style="background:var(--ord-${rank})"></span>` : '';
  return `<span class="tag">${swatch}${text}</span>`;
}

export function legend(items) {
  return `<div class="legend">${items
    .map(({ color, label, kind = 'swatch' }) => `<span class="legend-item"><span class="${kind}" style="background:${color}"></span>${esc(label)}</span>`)
    .join('')}</div>`;
}

export function scaleLegend(left, right) {
  return `<div class="scale-legend"><span>${esc(left)}</span>
    <span class="ramp" style="background:linear-gradient(90deg,var(--div-neg),var(--div-mid),var(--div-pos))"></span>
    <span>${esc(right)}</span></div>`;
}

// ------------------------------------------------------------ data table

/** Column sets of the stock tables; metrics missing from the data are skipped. */
export const COLUMN_SETS = [
  ['overview', 'Overview', ['market_cap', '1y_return', 'forward_pe', 'roe', 'revenue_growth', 'quality_score', 'valuation_category', 'technical_signal']],
  ['valuation', 'Valuation', ['forward_pe', 'trailing_pe', 'peg_ratio', 'price_to_book', 'price_to_sales', 'ev_to_ebitda', 'fcf_yield', 'dividend_yield', 'valuation_score', 'valuation_category']],
  ['profitability', 'Profitability & growth', ['gross_margin', 'operating_margin', 'profit_margin', 'roe', 'roa', 'roic', 'revenue_growth', 'earnings_growth']],
  ['health', 'Financial health', ['debt_to_equity', 'net_debt_to_ebitda', 'interest_coverage', 'current_ratio', 'quick_ratio', 'altman_z_score', 'z_score_zone']],
  ['performance', 'Performance & risk', ['1m_return', '3m_return', '6m_return', 'ytd_return', '1y_return', 'excess_return', 'volatility', 'max_drawdown', 'beta', 'sharpe_ratio', 'alpha']],
  ['technical', 'Technical & analysts', ['technical_signal', 'technical_score', 'rsi', 'price_vs_sma_200', 'adx', 'pct_from_52w_high', 'analyst_upside', 'recommendation_mean']],
];

export function columnSet(ds, key) {
  const set = COLUMN_SETS.find(([k]) => k === key) || COLUMN_SETS[0];
  return set[2].filter((k) => ds.has(k));
}

/** Cell HTML for a metric value in a table. */
export function cell(ds, key, stock) {
  const m = ds.metric(key);
  const v = stock[key];
  if (m?.fmt === 'label') return labelTag(key, v);
  const text = esc(value(m, v, { signed: m?.signed }));
  return m?.signed && m.better === 1 ? `<span class="${tone(v)}">${text}</span>` : text;
}

const compare = (a, b) => {
  const na = a === null || a === undefined || (typeof a === 'number' && !isNum(a));
  const nb = b === null || b === undefined || (typeof b === 'number' && !isNum(b));
  if (na || nb) return na === nb ? 0 : na ? 1 : -1; // missing values always last
  return typeof a === 'string' ? a.localeCompare(b) : a - b;
};

/**
 * Sortable table of stocks. Columns are metric keys; the first column is the
 * stock (ticker + company). Clicking a row calls onRowClick(ticker).
 */
export class StockTable {
  constructor(el, ds, { columns, sort = null, onSort = null, onRowClick = null, groupHeader = false, showSector = false }) {
    Object.assign(this, { el, ds, columns, sort, onSort, onRowClick, groupHeader, showSector, rows: [] });
    el.addEventListener('click', (e) => {
      const th = e.target.closest('th[data-key]');
      if (th) return this.toggleSort(th.dataset.key);
      const tr = e.target.closest('tr[data-ticker]');
      if (tr && this.onRowClick) this.onRowClick(tr.dataset.ticker);
    });
    el.addEventListener('keydown', (e) => {
      const tr = e.target.closest('tr[data-ticker]');
      if (tr && (e.key === 'Enter' || e.key === ' ') && this.onRowClick) {
        e.preventDefault();
        this.onRowClick(tr.dataset.ticker);
      }
    });
  }

  toggleSort(key) {
    const m = this.ds.metric(key);
    const textual = key === 'ticker' || key === 'sector' || m?.fmt === 'label';
    const firstDir = textual ? 'asc' : 'desc';
    this.sort = this.sort?.key === key
      ? { key, dir: this.sort.dir === 'asc' ? 'desc' : 'asc' }
      : { key, dir: firstDir };
    this.onSort?.(this.sort);
    this.render(this.rows);
    this.el.querySelector(`th[data-key="${CSS.escape(key)}"] button`)?.focus();
  }

  sortValue(stock, key) {
    const m = this.ds.metric(key);
    if (m?.fmt === 'label') return labelRank(key, stock[key]) ?? stock[key];
    return m ? this.ds.rankable(stock, key) : stock[key];
  }

  render(rows) {
    this.rows = rows;
    const { ds, columns, sort } = this;
    const sorted = sort
      ? [...rows].sort((a, b) => {
          const c = compare(this.sortValue(a, sort.key), this.sortValue(b, sort.key));
          const missing = this.sortValue(a, sort.key) == null || this.sortValue(b, sort.key) == null;
          return sort.dir === 'asc' || missing ? c : -c;
        })
      : rows;
    this.sorted = sorted;

    const ariaSort = (key) => (sort?.key === key ? ` aria-sort="${sort.dir === 'asc' ? 'ascending' : 'descending'}"` : '');
    const button = (label) => `<button type="button" class="th-sort">${esc(label)}</button>`;
    const head = [`<th class="sortable sticky-col" data-key="ticker"${ariaSort('ticker')}>${button('Stock')}</th>`]
      .concat(this.showSector ? [`<th class="sortable left" data-key="sector"${ariaSort('sector')}>${button('Sector')}</th>`] : [])
      .concat(columns.map((key) => {
        const m = ds.metric(key);
        const left = m?.fmt === 'label' ? ' left' : '';
        return `<th class="sortable${left}" data-key="${esc(key)}" title="${esc(m?.description || '')}"${ariaSort(key)}>${button(m?.label || key)}</th>`;
      }))
      .join('');

    let groupRow = '';
    if (this.groupHeader) {
      const spans = [];
      for (const key of columns) {
        const group = ds.metric(key)?.group || '';
        if (spans.length && spans[spans.length - 1].group === group) spans[spans.length - 1].n += 1;
        else spans.push({ group, n: 1 });
      }
      groupRow = `<tr class="group"><th class="sticky-col"></th>${this.showSector ? '<th></th>' : ''}${spans
        .map((s) => `<th colspan="${s.n}" class="left">${esc(s.group)}</th>`)
        .join('')}</tr>`;
    }

    const body = sorted
      .map((s) => `<tr data-ticker="${esc(s.ticker)}" tabindex="0">
        <td class="sticky-col"><span class="ticker">${esc(s.ticker)}</span><span class="company">${esc(s.name)}</span></td>
        ${this.showSector ? `<td class="left">${esc(s.sector)}</td>` : ''}
        ${columns.map((key) => `<td class="${ds.metric(key)?.fmt === 'label' ? 'left' : ''}">${cell(ds, key, s)}</td>`).join('')}
      </tr>`)
      .join('');

    this.el.innerHTML = `<table class="data"><thead>${groupRow}<tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }
}
