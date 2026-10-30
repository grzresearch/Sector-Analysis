// Hash routing: #/path?param=value. View state lives in the URL so every
// view is shareable; the `stock` parameter opens the stock panel on top of
// the current view without re-rendering it.

const state = { key: null, run: null };

function parseHash() {
  const [path, query = ''] = location.hash.replace(/^#/, '').split('?');
  return { path: path || '/', params: new URLSearchParams(query) };
}

const hashOf = (path, params) => {
  const query = params.toString();
  return `#${path}${query ? `?${query}` : ''}`;
};

/** A view is identified by its path and parameters, ignoring the stock panel. */
function viewKey(path, params) {
  const p = new URLSearchParams(params);
  p.delete('stock');
  return `${path}?${p}`;
}

/** Start routing: renderView(path, params) on view changes, renderStock(ticker) always. */
export function start(renderView, renderStock) {
  state.run = () => {
    const { path, params } = parseHash();
    const key = viewKey(path, params);
    if (key !== state.key) {
      state.key = key;
      renderView(path, params);
    }
    renderStock(params.get('stock'));
  };
  window.addEventListener('hashchange', state.run);
  state.run();
}

/** Render the current view again (e.g. after a theme change). */
export function refresh() {
  state.key = null;
  state.run();
}

/** Record view state in the URL without adding a history entry or re-rendering. */
export function setParams(updates) {
  const { path, params } = parseHash();
  for (const [k, v] of Object.entries(updates)) {
    if (v === null || v === undefined || v === '') params.delete(k);
    else params.set(k, v);
  }
  history.replaceState(null, '', hashOf(path, params));
  state.key = viewKey(path, params);
}

export function openStock(ticker) {
  const { path, params } = parseHash();
  params.set('stock', ticker);
  location.hash = hashOf(path, params);
}

export function closeStock() {
  const { path, params } = parseHash();
  if (!params.has('stock')) return;
  params.delete('stock');
  history.replaceState(null, '', hashOf(path, params));
  state.run();
}
