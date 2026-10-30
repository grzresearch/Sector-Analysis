// Color math in OKLab: perceptually even interpolation for the diverging
// scale, and the text color that stays legible on a filled cell.

const toLinear = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toGamma = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);

function hexToOklab(hex) {
  const n = parseInt(hex.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => toLinear(c / 255));
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

function oklabToHex([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const rgb = [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
  return `#${rgb
    .map((c) => Math.round(Math.min(1, Math.max(0, toGamma(c))) * 255).toString(16).padStart(2, '0'))
    .join('')}`;
}

/** Interpolate two colors in OKLab; t = 0 gives a, t = 1 gives b. */
export function mix(a, b, t) {
  const A = hexToOklab(a);
  const B = hexToOklab(b);
  return oklabToHex(A.map((v, i) => v + (B[i] - v) * t));
}

/** Near-black or white, whichever reads on the given fill. */
export const inkOn = (fill) => (hexToOklab(fill)[0] > 0.68 ? '#0b0b0b' : '#ffffff');

/**
 * Diverging color for t in [-1, 1]: unfavourable (red) through the neutral
 * midpoint to favourable (blue). `tokens` carries the theme's poles.
 */
export function diverging(t, tokens) {
  if (t === null || t === undefined || Number.isNaN(t)) return tokens.empty;
  const x = Math.max(-1, Math.min(1, t));
  return mix(tokens.mid, x < 0 ? tokens.neg : tokens.pos, Math.abs(x));
}
