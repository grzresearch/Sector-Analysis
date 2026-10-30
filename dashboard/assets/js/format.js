// Number formatting by the metric catalog's `fmt`, with a true minus sign.

const MINUS = '−';
const DASH = '—';

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);

function fixed(v, digits) {
  const s = Math.abs(v).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return v < 0 && Number(s.replace(/,/g, '')) !== 0 ? MINUS + s : s;
}

const withSign = (v, s) => (v > 0 && Number(s.replace(/[^0-9.]/g, '')) !== 0 ? `+${s}` : s);

export function cap(v) {
  if (!isNum(v)) return DASH;
  // Pick the unit from the rounded value, so $999.96B reads $1.00T, not $1,000B
  const a = Math.abs(v);
  if (a >= 999.5e9) return `$${fixed(v / 1e12, 2)}T`;
  if (a >= 999.5e6) return `$${fixed(v / 1e9, a >= 99.95e9 ? 0 : 1)}B`;
  if (a >= 1e6) return `$${fixed(v / 1e6, 0)}M`;
  return `$${fixed(v, 0)}`;
}

export function pct(v, { digits = 1, signed = false } = {}) {
  if (!isNum(v)) return DASH;
  const s = `${fixed(v * 100, digits)}%`;
  return signed ? withSign(v, s) : s;
}

export function number(v, digits = 2, { signed = false } = {}) {
  if (!isNum(v)) return DASH;
  const s = fixed(v, digits);
  return signed ? withSign(v, s) : s;
}

/** Format a value for a catalog metric. `signed` adds "+" to positive values. */
export function value(metric, v, { signed = false, short = false } = {}) {
  if (!metric) return isNum(v) ? number(v) : v ?? DASH;
  if (metric.fmt === 'label') return v ?? DASH;
  if (!isNum(v)) return DASH;
  switch (metric.fmt) {
    case 'pct':
      return pct(v, { signed, digits: short && Math.abs(v) >= 1 ? 0 : 1 });
    case 'pctpt': {
      const s = `${fixed(v, Math.abs(v) >= 100 ? 0 : 1)}%`;
      return signed ? withSign(v, s) : s;
    }
    case 'multiple':
      return `${fixed(v, Math.abs(v) >= 100 ? 0 : 1)}×`;
    case 'ratio':
      return number(v, 2, { signed });
    case 'num':
      return number(v, short || Math.abs(v) >= 100 ? 0 : 1, { signed });
    case 'int':
      return number(v, 0, { signed });
    case 'price':
      return `$${fixed(v, 2)}`;
    case 'cap':
      return cap(v);
    default:
      return number(v);
  }
}

/** Axis tick labels: compact and without trailing zeros. */
export function tick(metric, v) {
  if (!isNum(v)) return '';
  switch (metric?.fmt) {
    case 'pct':
      return `${fixed(v * 100, Math.abs(v) < 0.1 && v !== 0 && Math.round(v * 1000) % 10 ? 1 : 0)}%`;
    case 'pctpt':
      return `${fixed(v, 0)}%`;
    case 'multiple':
      return `${fixed(v, Math.abs(v) < 10 && !Number.isInteger(v) ? 1 : 0)}×`;
    case 'cap':
      // Drop trailing decimal zeros only: $1.50T -> $1.5T, $2.00T -> $2T, $500B stays
      return cap(v).replace(/(\.\d*?)0+(?=[TBM])/, '$1').replace(/\.(?=[TBM])/, '');
    case 'price':
      return `$${fixed(v, 0)}`;
    default:
      return Math.abs(v) >= 1000 ? fixed(v, 0) : String(Number(v.toPrecision(3))).replace('-', MINUS);
  }
}

export function date(iso, { year = true } = {}) {
  const d = new Date(`${iso}T00:00:00Z`);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    ...(year ? { year: 'numeric' } : {}),
    timeZone: 'UTC',
  });
}

/** Class name for signed values: pos / neg / ''. */
export const tone = (v) => (!isNum(v) || v === 0 ? '' : v > 0 ? 'pos' : 'neg');

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
/** Escape data before it goes into an HTML string (names come from the data feed). */
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ESCAPES[c]);
