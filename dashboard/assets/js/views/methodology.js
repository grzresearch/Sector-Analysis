// Methodology: where the data comes from, how every rating is built, and a
// glossary generated from the metric catalog.

import { date, esc } from '../format.js';

export const title = () => 'Methodology';

export function render(root, ds) {
  const { meta } = ds;
  const groups = new Map();
  for (const m of ds.metrics) {
    if (!groups.has(m.group)) groups.set(m.group, []);
    groups.get(m.group).push(m);
  }
  const direction = (m) => (m.better > 0 ? 'Higher is favourable' : m.better < 0 ? 'Lower is favourable' : '');

  root.innerHTML = `
    <header class="page-head">
      <div>
        <h1>Methodology</h1>
        <p class="lede">How the data is collected, how the ratings are computed, and what every metric means.</p>
      </div>
    </header>

    <div class="grid">
      <article class="card span-7 prose">
        <h3 style="margin-top:0">Data</h3>
        <p>${meta.mode === 'demo'
          ? '<strong style="color:var(--ink)">This build shows simulated demo data.</strong> Values are generated, not market data.'
          : `Fundamentals, analyst estimates and two years of daily prices come from ${esc(meta.source)}.`}
          The universe is the ${esc(meta.universe.name)}: ${meta.universe.analyzed} of ${meta.universe.size} constituents had enough data
          to be analysed. Prices are as of ${esc(date(meta.as_of))}; this build was generated ${esc(new Date(meta.generated_at).toUTCString())}.
          A scheduled GitHub Actions workflow reruns the analysis on weekdays after the US close and republishes this site.</p>
        <p>Sector assignments follow the 11 GICS sectors as listed with the index constituents; Yahoo Finance’s own
          classification only fills gaps. All sector statistics on this site are medians of the constituents unless stated
          otherwise, which keeps a single extreme stock from moving a sector. Valuation multiples count only where they are
          positive: a negative P/E means a loss, not a cheap stock, so it is shown but left out of medians, rankings and colours.</p>

        <h3>Sector indices</h3>
        <p>The cap-weighted index of a sector holds every constituent at today’s share count (market value divided by price),
          so each day’s return is weighted by the previous day’s market value, as in a sector ETF without rebalancing.
          A company with several listed share classes, such as Alphabet (GOOGL and GOOG), counts once: its market value is
          split across its listings, here and in every weight and total on this site.
          The equal-weighted index averages the constituents’ daily returns and shows how the typical stock fared.
          Both use dividend-adjusted closes. The benchmark is the SPDR S&amp;P 500 ETF (SPY).</p>

        <h3>Valuation rating</h3>
        <p>Each stock’s ratios are divided by its sector’s median, so a bank is compared with banks, not with software makers.
          The valuation score weights the relative forward P/E (30%), price to book (20%), debt to equity (15%), inverse ROE (15%),
          free cash flow yield (10%) and inverse net margin (10%). A score below 1 is cheaper than the sector peer group.
          The universe is then split into quintiles: 1 strongly undervalued, 2 undervalued, 3 fairly valued, 4 overvalued,
          5 strongly overvalued. By construction about 40% of stocks rate undervalued; what differs is where they cluster.</p>

        <h3>Performance rating</h3>
        <p>The performance score combines the 1-year return above the sector average (40%), revenue growth (20%),
          return on equity (20%) and the distance of the price from its 200-day average (20%), again split into quintiles
          from strong outperformer to strong underperformer.</p>

        <h3>Technical signal</h3>
        <p>Eight indicators vote with fixed points: RSI (15), MACD (15), moving averages including the golden cross (20),
          Bollinger Bands (10), stochastic (10), ADX trend direction (10), volume (10) and money flow (10).
          Bullish minus bearish points give the technical score from −100 to +100: 40 or more is a strong buy,
          20 or more a buy, −20 or less a sell, −40 or less a strong sell.</p>

        <h3>Quality and solvency</h3>
        <p>The quality score starts at 50 and adds or subtracts points for return on equity, net margin, current ratio,
          leverage, revenue growth and the PEG ratio, bounded to 0–100. The Altman Z-score combines working capital,
          retained earnings, EBIT, market value of equity and revenue, each scaled by total assets or liabilities.
          It was built for industrial companies, so it is not computed for financials, real estate and utilities, nor for
          companies whose statements are in another currency than their share price.</p>

        <h3>Factor models</h3>
        <p>An ordinary least-squares regression relates 1-year excess returns to eight characteristics
          (forward P/E, price to book, debt to equity, ROE, net margin, revenue growth, volatility, beta).
          Five machine learning models (ridge, lasso, elastic net, random forest, gradient boosting) try to predict 1-year returns
          from the same inputs and are scored on a held-out 20% of stocks. The Factor Lab reports both honestly, including when
          they explain little.</p>

        <h3>Limits</h3>
        <ul>
          <li>Fundamentals are the latest values reported to Yahoo Finance and can lag filings.</li>
          <li>History covers today’s constituents only, so stocks that left the index are missing (survivorship bias).</li>
          <li>Ratings are relative: “undervalued” means cheap compared with sector peers, not cheap in absolute terms.</li>
        </ul>
      </article>

      <aside class="card span-5 prose" style="align-self:start">
        <h3 style="margin-top:0">Reading the colors</h3>
        <p>One scale runs through every chart: <strong style="color:var(--pos-ink)">blue</strong> is favourable or up,
          <strong style="color:var(--neg-ink)">red</strong> is unfavourable or down, gray is neutral. “Favourable” follows each metric’s direction,
          so a low P/E and a high ROE are both blue. Sectors are told apart by position and labels, never by color alone.</p>
        <h3>Disclaimer</h3>
        <p>This site is a research and education project. It is not investment advice, and nothing here is a recommendation
          to buy or sell a security. Data may be delayed, incomplete or wrong.</p>
        <h3>Reproduce it</h3>
        <p>The analysis is open source. Run <code>sector-analysis --dashboard-data dashboard/data</code> and serve the
          <code>dashboard</code> folder to build this site locally.</p>
      </aside>
    </div>

    <section class="section">
      <div class="section-head"><h2>Glossary</h2><p>Every metric on this site, as computed by the analysis pipeline.</p></div>
      <div class="card flush"><div class="table-wrap">
        <table class="data glossary">
          <thead><tr><th>Metric</th><th class="left">Definition</th><th class="left">Direction</th></tr></thead>
          ${[...groups].map(([group, ms]) => `<tbody>
            <tr><td colspan="3" style="background:var(--surface-2);color:var(--ink-2);font-size:12px;letter-spacing:.04em;text-transform:uppercase">${esc(group)}</td></tr>
            ${ms.map((m) => `<tr><td>${esc(m.label)}</td><td>${esc(m.description)}</td><td class="muted">${esc(direction(m))}</td></tr>`).join('')}
          </tbody>`).join('')}
        </table>
      </div></div>
    </section>`;
}
