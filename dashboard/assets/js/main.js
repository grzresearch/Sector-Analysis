// Entry point: load the data, then route between views.

import { loadDataset } from './store.js';
import { disposeCharts } from './charts.js';
import { date, esc } from './format.js';
import { start, refresh, openStock } from './router.js';
import { renderStock } from './drawer.js';
import * as overview from './views/overview.js';
import * as sectors from './views/sector.js';
import * as screener from './views/screener.js';
import * as lab from './views/lab.js';
import * as methodology from './views/methodology.js';

const VIEWS = {
  '': overview,
  sector: sectors,
  screener,
  lab,
  methodology,
};

const main = document.getElementById('view');

function renderView(ds, path, params) {
  const segments = path.split('/').filter(Boolean);
  const view = VIEWS[segments[0] || ''] || overview;

  disposeCharts(main);
  main.innerHTML = '';
  view.render(main, ds, { segments, params });

  const section = `/${segments[0] || ''}`;
  for (const a of document.querySelectorAll('.nav a')) {
    if (a.dataset.route === section) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  }
  document.title = view.title ? `${view.title(ds, segments)} · Sector Analysis` : 'Sector Analysis';
  window.scrollTo({ top: 0 });
}

// ------------------------------------------------------------ search

function initSearch(ds) {
  const input = document.getElementById('search');
  const list = document.getElementById('search-results');
  let matches = [];
  let active = 0;

  const close = () => {
    list.hidden = true;
    input.setAttribute('aria-expanded', 'false');
  };

  const choose = (ticker) => {
    close();
    input.value = '';
    input.blur();
    openStock(ticker);
  };

  const paint = () => {
    list.innerHTML = matches.length
      ? matches
          .map((s, i) => `<li role="option" id="opt-${i}" data-ticker="${esc(s.ticker)}" aria-selected="${i === active}">
            <span class="ticker">${esc(s.ticker)}</span><span class="name">${esc(s.name)}</span><span class="sector">${esc(s.sector)}</span></li>`)
          .join('')
      : '<li class="empty">No matching stock</li>';
    input.setAttribute('aria-activedescendant', matches.length ? `opt-${active}` : '');
  };

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    if (!q) return close();
    const score = (s) => {
      const t = s.ticker.toLowerCase();
      const n = (s.name || '').toLowerCase();
      if (t === q) return 0;
      if (t.startsWith(q)) return 1;
      if (n.startsWith(q)) return 2;
      if (n.includes(q)) return 3;
      return t.includes(q) ? 4 : 9;
    };
    matches = ds.stocks
      .map((s) => [score(s), s])
      .filter(([sc]) => sc < 9)
      .sort((a, b) => a[0] - b[0] || (b[1].market_cap || 0) - (a[1].market_cap || 0))
      .slice(0, 8)
      .map(([, s]) => s);
    active = 0;
    paint();
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!matches.length) return;
      active = (active + (e.key === 'ArrowDown' ? 1 : matches.length - 1)) % matches.length;
      paint();
    } else if (e.key === 'Enter' && matches[active]) {
      choose(matches[active].ticker);
    } else if (e.key === 'Escape') {
      input.value = '';
      close();
      input.blur();
    }
  });

  list.addEventListener('mousedown', (e) => {
    const li = e.target.closest('li[data-ticker]');
    if (li) {
      e.preventDefault();
      choose(li.dataset.ticker);
    }
  });
  input.addEventListener('blur', () => setTimeout(close, 100));

  document.addEventListener('keydown', (e) => {
    const typing = /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement?.tagName);
    if (e.key === '/' && !typing && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      input.focus();
    }
  });
}

// ------------------------------------------------------------ chrome

function initTheme() {
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem('theme', next);
    } catch {
      /* storage unavailable: the choice lasts for this page view */
    }
    refresh();
  });
}

function showProvenance(ds) {
  const { meta } = ds;
  const badge = document.getElementById('data-badge');
  badge.hidden = false;
  badge.classList.toggle('demo', meta.mode === 'demo');
  badge.textContent = meta.mode === 'demo' ? 'Demo data' : `Live · ${date(meta.as_of)}`;
  badge.title = `${meta.source}, generated ${new Date(meta.generated_at).toUTCString()}`;

  const { analyzed, size } = meta.universe;
  document.getElementById('footer-source').textContent =
    `${meta.source} · ${analyzed} of ${size} ${meta.universe.name} constituents · prices as of ${date(meta.as_of)}`;
}

function showError(error) {
  main.innerHTML = `<div class="error-state">
    <h1>The market data could not be loaded</h1>
    <p>${esc(error.message)}</p>
    <p style="margin-top:12px">Generate it with <code>sector-analysis --dashboard-data dashboard/data</code>
      and serve the <code>dashboard</code> folder over HTTP.</p></div>`;
}

async function boot() {
  initTheme();
  let ds;
  try {
    ds = await loadDataset();
  } catch (error) {
    showError(error);
    return;
  }
  if (!window.echarts) {
    showError(new Error('The charting library failed to load. Check your connection and reload.'));
    return;
  }
  showProvenance(ds);
  initSearch(ds);
  start(
    (path, params) => renderView(ds, path, params),
    (ticker) => renderStock(ds, ticker),
  );
}

// ECharts is a deferred classic script; module scripts run after it.
boot();
