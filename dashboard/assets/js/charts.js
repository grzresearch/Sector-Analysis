// ECharts glue: theme from CSS tokens, lifecycle, shared axes and tooltips.

import { esc, tick } from './format.js';

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/** Current theme tokens (re-read after every theme switch). */
export function tokens() {
  return {
    surface: css('--surface'),
    surface2: css('--surface-2'),
    surface3: css('--surface-3'),
    ink: css('--ink'),
    ink2: css('--ink-2'),
    muted: css('--muted'),
    grid: css('--grid'),
    axis: css('--axis'),
    border: css('--border'),
    accent: css('--accent'),
    context: css('--context'),
    pos: css('--pos'),
    neg: css('--neg'),
    neutral: css('--ord-3'),
    divNeg: css('--div-neg'),
    divMid: css('--div-mid'),
    divPos: css('--div-pos'),
    ord: [1, 2, 3, 4, 5].map((i) => css(`--ord-${i}`)),
    font: css('--font'),
    empty: css('--surface-2'),
  };
}

/** Diverging scale tokens in the shape colors.diverging() expects. */
export const divergingTokens = (t) => ({ neg: t.divNeg, mid: t.divMid, pos: t.divPos, empty: t.empty });

// ------------------------------------------------------------ lifecycle

const live = new Set();
const resizer = new ResizeObserver((entries) => {
  for (const entry of entries) window.echarts.getInstanceByDom(entry.target)?.resize();
});

export function createChart(el) {
  const chart = window.echarts.init(el, null, { renderer: 'svg' });
  live.add(chart);
  resizer.observe(el);
  return chart;
}

/** Dispose every chart inside `root` (default: all). */
export function disposeCharts(root = document) {
  for (const chart of live) {
    const el = chart.getDom();
    if (root === document || root.contains(el)) {
      resizer.unobserve(el);
      chart.dispose();
      live.delete(chart);
    }
  }
}

// ------------------------------------------------------------ options

export function tooltip(t, extra = {}) {
  return {
    confine: true,
    backgroundColor: t.surface,
    borderColor: t.border,
    borderWidth: 1,
    padding: [8, 11],
    textStyle: { color: t.ink, fontFamily: t.font, fontSize: 12 },
    extraCssText: 'border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.14);',
    ...extra,
  };
}

export function base(t) {
  return {
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    animationDuration: 350,
    animationDurationUpdate: 250,
    textStyle: { fontFamily: t.font, color: t.ink2, fontSize: 12 },
    tooltip: tooltip(t),
  };
}

export function valueAxis(t, { metric = null, formatter = null, ...rest } = {}) {
  return {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid, width: 1 } },
    axisLabel: {
      color: t.muted,
      fontSize: 11,
      formatter: formatter || ((v) => tick(metric, v)),
    },
    nameTextStyle: { color: t.muted, fontSize: 11.5 },
    ...rest,
  };
}

export function categoryAxis(t, data, rest = {}) {
  return {
    type: 'category',
    data,
    axisLine: { lineStyle: { color: t.axis } },
    axisTick: { show: false },
    axisLabel: { color: t.ink2, fontSize: 12 },
    ...rest,
  };
}

/**
 * Tooltip body: a title, then rows of [key, label, value]. The value leads in
 * strong ink; series are keyed by a short line in their color.
 */
export function tooltipHtml(title, rows = [], note = '') {
  const body = rows
    .map(([color, label, value]) => {
      const key = color
        ? `<span style="display:inline-block;width:10px;height:2px;border-radius:1px;background:${color};margin-right:6px;vertical-align:middle"></span>`
        : '';
      return `<div style="display:flex;justify-content:space-between;gap:16px;line-height:1.7">
        <span style="color:var(--ink-2)">${key}${esc(label)}</span>
        <strong style="font-weight:600;font-variant-numeric:tabular-nums">${esc(value)}</strong></div>`;
    })
    .join('');
  const head = title ? `<div style="font-weight:600;margin-bottom:4px">${esc(title)}</div>` : '';
  const foot = note ? `<div style="margin-top:4px;color:var(--muted);font-size:11.5px">${esc(note)}</div>` : '';
  return head + body + foot;
}

/**
 * Place every point label of a rendered scatter series where it collides
 * least with the markers and the labels placed before it (right, left, top
 * or bottom of its marker), so no point loses its name.
 */
export function placeLabels(chart, seriesIndex, { font, gap = 5, height = 14 } = {}) {
  const series = chart.getOption().series[seriesIndex];
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = font;
  const width = chart.getWidth();
  const bottom = chart.getHeight();

  const points = series.data.map((d) => {
    const [x, y] = chart.convertToPixel({ seriesIndex }, d.value);
    return { x, y, r: (d.symbolSize ?? series.symbolSize ?? 10) / 2 };
  });
  const taken = points.map(({ x, y, r }) => ({ x0: x - r, y0: y - r, x1: x + r, y1: y + r }));
  const overlap = (a, b) =>
    Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0)) * Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));

  const positions = series.data.map((d, i) => {
    const { x, y, r } = points[i];
    const w = ctx.measureText(d.name).width;
    const candidates = {
      right: { x0: x + r + gap, x1: x + r + gap + w, y0: y - height / 2, y1: y + height / 2 },
      left: { x0: x - r - gap - w, x1: x - r - gap, y0: y - height / 2, y1: y + height / 2 },
      top: { x0: x - w / 2, x1: x + w / 2, y0: y - r - gap - height, y1: y - r - gap },
      bottom: { x0: x - w / 2, x1: x + w / 2, y0: y + r + gap, y1: y + r + gap + height },
    };
    let best = null;
    for (const [position, box] of Object.entries(candidates)) {
      const outside = box.x0 < 0 || box.x1 > width || box.y0 < 0 || box.y1 > bottom;
      const cost = (outside ? 1e9 : 0) + taken.reduce((c, other, j) => c + (j === i ? 0 : overlap(box, other)), 0);
      if (!best || cost < best.cost) best = { position, box, cost };
    }
    taken.push(best.box);
    return best.position;
  });

  chart.setOption({
    series: chart.getOption().series.map((s, k) => (k === seriesIndex
      ? { data: s.data.map((d, i) => ({ ...d, label: { ...d.label, position: positions[i] } })) }
      : {})),
  });
}

/**
 * Nearest-point hover for dense scatters: the pointer only has to be closest
 * to a point (within `radius` px), not on it. `onClick` receives the data index.
 */
export function nearestPointHover(chart, seriesIndex, { radius = 28, onClick = null } = {}) {
  let current = -1;
  const zr = chart.getZr();

  const nearest = (x, y) => {
    const data = chart.getOption().series[seriesIndex].data;
    let best = -1;
    let bestDist = radius * radius;
    data.forEach((d, i) => {
      const value = d.value ?? d;
      const p = chart.convertToPixel({ seriesIndex }, [value[0], value[1]]);
      if (!p) return;
      const dist = (p[0] - x) ** 2 + (p[1] - y) ** 2;
      if (dist < bestDist) {
        bestDist = dist;
        best = i;
      }
    });
    return best;
  };

  const show = (i) => {
    if (i === current) return;
    if (current >= 0) chart.dispatchAction({ type: 'downplay', seriesIndex, dataIndex: current });
    current = i;
    if (i >= 0) {
      chart.dispatchAction({ type: 'highlight', seriesIndex, dataIndex: i });
      chart.dispatchAction({ type: 'showTip', seriesIndex, dataIndex: i });
    } else {
      chart.dispatchAction({ type: 'hideTip' });
    }
  };

  zr.on('mousemove', (e) => {
    show(nearest(e.offsetX, e.offsetY));
    if (onClick) zr.setCursorStyle(current >= 0 ? 'pointer' : 'default');
  });
  zr.on('globalout', () => show(-1));
  zr.on('click', (e) => {
    const i = nearest(e.offsetX, e.offsetY);
    if (i >= 0 && onClick) onClick(i);
  });
}
