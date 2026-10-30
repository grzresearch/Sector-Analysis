// The dataset the dashboard renders: dashboard.json turned into stock objects,
// plus the lookups and period math every view shares.

import { isNum, median, percentileRank, sum } from './stats.js';

export const VALUATION_ORDER = [
  'Strongly Undervalued',
  'Undervalued',
  'Fairly Valued',
  'Overvalued',
  'Strongly Overvalued',
];
const PERFORMANCE_ORDER = [
  'Strong Outperformer',
  'Outperformer',
  'Market Performer',
  'Underperformer',
  'Strong Underperformer',
];
export const SIGNAL_ORDER = ['Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'];
export const ZONE_STATUS = { 'Safe Zone': 'good', 'Grey Zone': 'warning', 'Distress Zone': 'critical' };

/** Ordered labels of a categorical metric, best first. */
export const LABEL_ORDERS = {
  valuation_category: VALUATION_ORDER,
  performance_category: PERFORMANCE_ORDER,
  technical_signal: SIGNAL_ORDER,
};

/** Look-back windows in trading days; YTD and 2Y are resolved from the dates. */
const PERIODS = [
  { key: '1W', days: 5, metric: '1w_return' },
  { key: '1M', days: 21, metric: '1m_return' },
  { key: '3M', days: 63, metric: '3m_return' },
  { key: '6M', days: 126, metric: '6m_return' },
  { key: 'YTD', metric: 'ytd_return' },
  { key: '1Y', days: 252, metric: '1y_return' },
  { key: '2Y', metric: null },
];

export const slugify = (s) =>
  String(s).toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export class Dataset {
  constructor(raw) {
    this.meta = raw.meta;
    this.metrics = raw.metrics;
    this.history = raw.history || null;
    this.models = raw.models || {};
    this.metricByKey = new Map(this.metrics.map((m) => [m.key, m]));

    const { columns, rows } = raw.stocks;
    this.stocks = rows.map((row) => Object.fromEntries(columns.map((c, i) => [c, row[i]])));
    this.byTicker = new Map(this.stocks.map((s) => [s.ticker, s]));

    const caps = new Map();
    for (const s of this.stocks) caps.set(s.sector, (caps.get(s.sector) || 0) + (s.market_cap || 0));
    this.sectorCap = caps;
    this.totalCap = sum([...caps.values()]);
    this.sectors = [...caps.keys()].sort((a, b) => caps.get(b) - caps.get(a));
    this.sectorStocks = new Map(this.sectors.map((sec) => [sec, this.stocks.filter((s) => s.sector === sec)]));

    // Metrics that take both signs show "+" on positive values (and tone them, if directional)
    for (const m of this.metrics) {
      m.signed = m.fmt !== 'label' && this.stocks.some((s) => s[m.key] < 0) && this.stocks.some((s) => s[m.key] > 0);
    }
  }

  metric(key) {
    return this.metricByKey.get(key);
  }

  has(key) {
    return this.metricByKey.has(key);
  }

  /** Numeric metrics fit for axes, rankings and heat maps. */
  numericMetrics() {
    return this.metrics.filter((m) => m.fmt !== 'label' && m.fmt !== 'price');
  }

  sectorFromSlug(slug) {
    return this.sectors.find((s) => slugify(s) === slug) || null;
  }

  peers(sector) {
    return sector ? this.sectorStocks.get(sector) || [] : this.stocks;
  }

  values(key, stocks = this.stocks) {
    return stocks.map((s) => s[key]);
  }

  median(key, stocks = this.stocks) {
    return median(this.values(key, stocks));
  }

  /** Share (0-1) of stocks carrying one of the given labels, among those labelled. */
  share(key, labels, stocks = this.stocks) {
    const labelled = stocks.filter((s) => s[key]);
    return labelled.length ? labelled.filter((s) => labels.includes(s[key])).length / labelled.length : null;
  }

  /**
   * Percentile (0-100) of a stock's value among peers, oriented so that 100 is
   * the most favourable end for metrics with a direction.
   */
  favourability(stock, key, peers = this.stocks) {
    const p = percentileRank(this.values(key, peers), stock[key]);
    if (p === null) return null;
    return this.metric(key)?.better === -1 ? 100 - p : p;
  }

  // ------------------------------------------------------------ history

  /** Index into history.dates where a look-back period starts. */
  periodStart(periodKey) {
    const dates = this.history?.dates || [];
    const last = dates.length - 1;
    if (last < 1) return 0;
    const period = PERIODS.find((p) => p.key === periodKey);
    if (period?.days) return Math.max(0, last - period.days);
    if (periodKey === 'YTD') {
      const year = dates[last].slice(0, 4);
      const first = dates.findIndex((d) => d.slice(0, 4) === year);
      return Math.max(0, first - 1); // base: last close of the previous year
    }
    return 0;
  }

  /** Total return of an index series from `start` to the latest value. */
  static seriesReturn(series, start) {
    let i = start;
    while (i < series.length && !isNum(series[i])) i += 1;
    const end = series.length - 1;
    return i < end && isNum(series[end]) ? series[end] / series[i] - 1 : null;
  }

  sectorSeries(sector, weighting = 'cap') {
    return this.history?.sectors?.[sector]?.[weighting] || null;
  }

  benchmarkSeries(name = this.meta.benchmark) {
    return this.history?.benchmarks?.[name] || null;
  }

  /** Sector return over a period: from the index when there is history, else the median stock. */
  sectorReturn(sector, periodKey, weighting = 'cap') {
    const series = this.sectorSeries(sector, weighting);
    if (series) return Dataset.seriesReturn(series, this.periodStart(periodKey));
    const metric = PERIODS.find((p) => p.key === periodKey)?.metric;
    return metric && this.has(metric) ? this.median(metric, this.peers(sector)) : null;
  }

  benchmarkReturn(periodKey) {
    const series = this.benchmarkSeries();
    return series ? Dataset.seriesReturn(series, this.periodStart(periodKey)) : null;
  }

  /** Periods the data can answer. */
  availablePeriods() {
    return PERIODS.filter((p) => (this.history ? true : p.metric && this.has(p.metric)));
  }

  // ------------------------------------------------------------ weekly prices (lazy)

  prices() {
    if (!this.history) return Promise.resolve(null);
    this.pricesPromise ??= fetch('data/prices.json')
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
    return this.pricesPromise;
  }
}

export async function loadDataset(url = 'data/dashboard.json') {
  const response = await fetch(url, { cache: 'no-cache' });
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return new Dataset(await response.json());
}
