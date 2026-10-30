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
  history.replaceState(history.state, '', hashOf(path, params));
  state.key = viewKey(path, params);
}

/**
 * Open the stock panel as one history entry: switching stocks inside the panel
 * replaces it, and closing goes back, so Back never lands on a closed panel.
 */
export function openStock(ticker) {
  const { path, params } = parseHash();
  params.set('stock', ticker);
  if (history.state?.panel) history.replaceState({ panel: true }, '', hashOf(path, params));
  else history.pushState({ panel: true }, '', hashOf(path, params));
  state.run();
}

export function closeStock() {
  const { path, params } = parseHash();
  if (!params.has('stock')) return;
  if (history.state?.panel) {
    history.back(); // the hashchange that follows closes the panel
    return;
  }
  // Opened from a shared link: there is no entry to go back to
  params.delete('stock');
  history.replaceState(null, '', hashOf(path, params));
  state.run();
}
