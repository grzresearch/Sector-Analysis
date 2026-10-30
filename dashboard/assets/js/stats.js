// Small, dependency-free statistics on arrays of numbers.

export const isNum = (v) => typeof v === 'number' && Number.isFinite(v);

const finite = (values) => values.filter(isNum);

export const sum = (values) => finite(values).reduce((a, b) => a + b, 0);

export function mean(values) {
  const xs = finite(values);
  return xs.length ? sum(xs) / xs.length : null;
}

export function std(values) {
  const xs = finite(values);
  if (xs.length < 2) return null;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((a, x) => a + (x - m) ** 2, 0) / (xs.length - 1));
}

/** Quantile with linear interpolation (the default of numpy and pandas). */
export function quantile(values, q) {
  const xs = finite(values).sort((a, b) => a - b);
  if (!xs.length) return null;
  const pos = (xs.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo);
}

export const median = (values) => quantile(values, 0.5);

/** Percentile rank (0-100) of v among values: share of values below plus half the ties. */
export function percentileRank(values, v) {
  const xs = finite(values);
  if (!xs.length || !isNum(v)) return null;
  let below = 0;
  let equal = 0;
  for (const x of xs) {
    if (x < v) below += 1;
    else if (x === v) equal += 1;
  }
  return (100 * (below + equal / 2)) / xs.length;
}

/** Average ranks (1-based), ties share their mean rank. */
function ranks(xs) {
  const order = xs.map((x, i) => [x, i]).sort((a, b) => a[0] - b[0]);
  const r = new Array(xs.length);
  for (let i = 0; i < order.length; ) {
    let j = i;
    while (j + 1 < order.length && order[j + 1][0] === order[i][0]) j += 1;
    const rank = (i + j) / 2 + 1;
    for (let k = i; k <= j; k += 1) r[order[k][1]] = rank;
    i = j + 1;
  }
  return r;
}

/** Keep only the index positions where both series are finite. */
function pairs(xs, ys) {
  const a = [];
  const b = [];
  for (let i = 0; i < xs.length; i += 1) {
    if (isNum(xs[i]) && isNum(ys[i])) {
      a.push(xs[i]);
      b.push(ys[i]);
    }
  }
  return [a, b];
}

export function pearson(xs, ys) {
  const [a, b] = pairs(xs, ys);
  if (a.length < 3) return null;
  const ma = mean(a);
  const mb = mean(b);
  let sab = 0;
  let saa = 0;
  let sbb = 0;
  for (let i = 0; i < a.length; i += 1) {
    sab += (a[i] - ma) * (b[i] - mb);
    saa += (a[i] - ma) ** 2;
    sbb += (b[i] - mb) ** 2;
  }
  return saa && sbb ? sab / Math.sqrt(saa * sbb) : null;
}

export function spearman(xs, ys) {
  const [a, b] = pairs(xs, ys);
  return a.length < 3 ? null : pearson(ranks(a), ranks(b));
}

/** Ordinary least squares y = intercept + slope * x. */
export function linearFit(xs, ys) {
  const [a, b] = pairs(xs, ys);
  if (a.length < 3) return null;
  const ma = mean(a);
  const mb = mean(b);
  let sab = 0;
  let saa = 0;
  for (let i = 0; i < a.length; i += 1) {
    sab += (a[i] - ma) * (b[i] - mb);
    saa += (a[i] - ma) ** 2;
  }
  if (!saa) return null;
  const slope = sab / saa;
  const r = pearson(a, b);
  return { slope, intercept: mb - slope * ma, r2: r === null ? null : r * r, n: a.length };
}

/** Tukey box: whiskers at the most extreme points within 1.5 IQR. */
export function box(values) {
  const xs = finite(values).sort((a, b) => a - b);
  if (!xs.length) return null;
  const q1 = quantile(xs, 0.25);
  const q2 = quantile(xs, 0.5);
  const q3 = quantile(xs, 0.75);
  const iqr = q3 - q1;
  const inside = xs.filter((x) => x >= q1 - 1.5 * iqr && x <= q3 + 1.5 * iqr);
  return {
    low: inside[0],
    q1,
    median: q2,
    q3,
    high: inside[inside.length - 1],
    outliers: xs.filter((x) => x < q1 - 1.5 * iqr || x > q3 + 1.5 * iqr),
    n: xs.length,
  };
}

/** Daily simple returns of a price or index series (null where undefined). */
export function returns(levels) {
  return levels.map((v, i) => (i && isNum(v) && isNum(levels[i - 1]) && levels[i - 1] ? v / levels[i - 1] - 1 : null));
}
