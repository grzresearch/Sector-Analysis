"""
Dashboard Data Export
Writes the analysis results as JSON for the interactive web dashboard (dashboard/)

The dashboard is a static site, so everything it shows comes from two files:
- dashboard.json: metric catalog, one row per stock, sector and benchmark
  price indices, and the regression / machine learning diagnostics
- prices.json: weekly closes per stock for the stock detail panel
  (loaded on demand)
"""

import json
import math
import os
from collections import namedtuple
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .regression_models import prepare_regression_data, get_feature_importance

SCHEMA_VERSION = 1

# =============================================================================
# METRIC CATALOG
# What the dashboard knows about each metric: a metric listed here (and
# present in the data) appears in the screener conditions, the Factor Lab
# pickers, the stock panel, the CSV export and the glossary. The table column
# sets and the fixed lists of the Overview and Sector views are chosen in the
# dashboard's JavaScript (COLUMN_SETS in dashboard/assets/js/components.js).
#
# fmt           - how the value is displayed:
#                 pct (fraction shown as %), pctpt (already in percent points),
#                 multiple (x), ratio, num, int, price, cap, label (categorical)
# better        - +1 when higher is favourable, -1 when lower is, 0 when neutral
# positive_only - only positive values are meaningful (a negative P/E means a
#                 loss, not a cheap stock), so others are left out of rankings
# =============================================================================

Metric = namedtuple('Metric', 'key label group fmt better description positive_only', defaults=(False,))

METRICS = [
    # Profile
    Metric('current_price', 'Price', 'Profile', 'price', 0,
           'Last close in USD.'),
    Metric('market_cap', 'Market cap', 'Profile', 'cap', 0,
           'Market value of the whole company, across all of its share classes.'),

    # Valuation
    Metric('forward_pe', 'Forward P/E', 'Valuation', 'multiple', -1,
           'Price divided by the consensus earnings estimate for the next fiscal year.', True),
    Metric('trailing_pe', 'Trailing P/E', 'Valuation', 'multiple', -1,
           'Price divided by earnings per share over the last twelve months.', True),
    Metric('peg_ratio', 'PEG ratio', 'Valuation', 'ratio', -1,
           'P/E divided by expected earnings growth; below 1 suggests growth is cheaply priced.', True),
    Metric('price_to_book', 'Price / book', 'Valuation', 'multiple', -1,
           "Market cap divided by shareholders' equity.", True),
    Metric('price_to_sales', 'Price / sales', 'Valuation', 'multiple', -1,
           'Market cap divided by trailing twelve-month revenue.', True),
    Metric('ev_to_ebitda', 'EV / EBITDA', 'Valuation', 'multiple', -1,
           'Enterprise value divided by EBITDA; compares companies regardless of capital structure.', True),
    Metric('ev_to_revenue', 'EV / revenue', 'Valuation', 'multiple', -1,
           'Enterprise value divided by trailing twelve-month revenue.', True),
    Metric('fcf_yield', 'FCF yield', 'Valuation', 'pct', 1,
           'Free cash flow divided by market cap.'),
    Metric('dividend_yield', 'Dividend yield', 'Valuation', 'pct', 1,
           'Forward annual dividend divided by price.'),

    # Profitability
    Metric('gross_margin', 'Gross margin', 'Profitability', 'pct', 1,
           'Gross profit divided by revenue.'),
    Metric('operating_margin', 'Operating margin', 'Profitability', 'pct', 1,
           'Operating income divided by revenue.'),
    Metric('profit_margin', 'Net margin', 'Profitability', 'pct', 1,
           'Net income divided by revenue.'),
    Metric('ebitda_margin', 'EBITDA margin', 'Profitability', 'pct', 1,
           'EBITDA divided by revenue.'),
    Metric('roe', 'Return on equity', 'Profitability', 'pct', 1,
           "Net income divided by shareholders' equity."),
    Metric('roa', 'Return on assets', 'Profitability', 'pct', 1,
           'Net income divided by total assets.'),
    Metric('roic', 'Return on invested capital', 'Profitability', 'pct', 1,
           'Net income divided by debt plus equity minus cash.'),

    # Growth
    Metric('revenue_growth', 'Revenue growth', 'Growth', 'pct', 1,
           'Year-over-year revenue growth of the most recent quarter.'),
    Metric('earnings_growth', 'Earnings growth', 'Growth', 'pct', 1,
           'Year-over-year earnings growth of the most recent quarter.'),

    # Financial health
    Metric('debt_to_equity', 'Debt / equity', 'Financial health', 'pctpt', -1,
           "Total debt divided by shareholders' equity."),
    Metric('net_debt_to_ebitda', 'Net debt / EBITDA', 'Financial health', 'multiple', -1,
           'Debt minus cash, in years of EBITDA.'),
    Metric('interest_coverage', 'Interest coverage', 'Financial health', 'multiple', 1,
           'EBIT divided by interest expense; above 3 is considered safe.'),
    Metric('current_ratio', 'Current ratio', 'Financial health', 'ratio', 1,
           'Current assets divided by current liabilities.'),
    Metric('quick_ratio', 'Quick ratio', 'Financial health', 'ratio', 1,
           'Current assets excluding inventory divided by current liabilities.'),

    # Returns
    Metric('1w_return', '1W return', 'Returns', 'pct', 1,
           'Total return (dividends reinvested) over the last 5 trading days.'),
    Metric('1m_return', '1M return', 'Returns', 'pct', 1,
           'Total return (dividends reinvested) over the last 21 trading days.'),
    Metric('3m_return', '3M return', 'Returns', 'pct', 1,
           'Total return (dividends reinvested) over the last 63 trading days.'),
    Metric('6m_return', '6M return', 'Returns', 'pct', 1,
           'Total return (dividends reinvested) over the last 126 trading days.'),
    Metric('ytd_return', 'YTD return', 'Returns', 'pct', 1,
           'Total return (dividends reinvested) since the last close of the previous year.'),
    Metric('1y_return', '1Y return', 'Returns', 'pct', 1,
           'Total return (dividends reinvested) over the last 252 trading days.'),
    Metric('excess_return', 'Excess return vs sector', 'Returns', 'pct', 1,
           '1-year return minus the average 1-year return of the sector.'),

    # Risk
    Metric('volatility', 'Volatility', 'Risk', 'pct', -1,
           'Annualised standard deviation of daily returns over two years.'),
    Metric('downside_volatility', 'Downside volatility', 'Risk', 'pct', -1,
           'Annualised standard deviation of the negative daily returns.'),
    Metric('max_drawdown', 'Max drawdown', 'Risk', 'pct', 1,
           'Largest peak-to-trough decline over two years.'),
    Metric('var_95', 'VaR (95%)', 'Risk', 'pct', 1,
           'Daily loss exceeded on only 5% of days (historical value at risk).'),
    Metric('cvar_95', 'CVaR (95%)', 'Risk', 'pct', 1,
           'Average daily loss on the worst 5% of days (expected shortfall).'),
    Metric('beta', 'Beta', 'Risk', 'ratio', 0,
           'Sensitivity to the S&P 500; above 1 moves more than the market.'),

    # Risk-adjusted performance
    Metric('sharpe_ratio', 'Sharpe ratio', 'Risk-adjusted', 'ratio', 1,
           'Annualised return above a 4% risk-free rate per unit of volatility.'),
    Metric('sortino_ratio', 'Sortino ratio', 'Risk-adjusted', 'ratio', 1,
           'Like the Sharpe ratio, but only penalises downside volatility.'),
    Metric('calmar_ratio', 'Calmar ratio', 'Risk-adjusted', 'ratio', 1,
           'Annualised return divided by the maximum drawdown.'),
    Metric('omega_ratio', 'Omega ratio', 'Risk-adjusted', 'ratio', 1,
           'Sum of daily gains divided by sum of daily losses.'),
    Metric('alpha', 'Alpha', 'Risk-adjusted', 'pct', 1,
           "Annualised return not explained by the stock's market exposure (Jensen's alpha vs SPY)."),
    Metric('information_ratio', 'Information ratio', 'Risk-adjusted', 'ratio', 1,
           'Annualised return above SPY divided by the tracking error.'),
    Metric('tracking_error', 'Tracking error', 'Risk-adjusted', 'pct', 0,
           'Annualised volatility of the return difference to SPY.'),
    Metric('r_squared', 'R-squared vs SPY', 'Risk-adjusted', 'ratio', 0,
           'Share of daily return variance explained by the S&P 500.'),
    Metric('up_capture', 'Up capture', 'Risk-adjusted', 'pctpt', 1,
           'Average return on days SPY rose, relative to SPY; above 100 beats the market.'),
    Metric('down_capture', 'Down capture', 'Risk-adjusted', 'pctpt', -1,
           'Average return on days SPY fell, relative to SPY; below 100 loses less.'),

    # Technical
    Metric('technical_signal', 'Technical signal', 'Technical', 'label', 0,
           'Summary of RSI, MACD, moving averages, Bollinger Bands, stochastic, ADX, volume and money flow.'),
    Metric('technical_score', 'Technical score', 'Technical', 'int', 1,
           'Bullish minus bearish indicator points, from -100 to +100.'),
    Metric('price_vs_sma_200', 'Price vs 200-day SMA', 'Technical', 'pct', 1,
           'Distance of the price from its 200-day simple moving average.'),
    Metric('rsi', 'RSI (14)', 'Technical', 'num', 0,
           'Relative Strength Index; below 30 is oversold, above 70 overbought.'),
    Metric('stoch_k', 'Stochastic %K', 'Technical', 'num', 0,
           'Position of the close in the 14-day range; below 20 oversold, above 80 overbought.'),
    Metric('mfi', 'Money flow index', 'Technical', 'num', 0,
           'Volume-weighted RSI; below 20 oversold, above 80 overbought.'),
    Metric('adx', 'ADX', 'Technical', 'num', 0,
           'Average Directional Index; above 25 indicates a strong trend.'),
    Metric('bb_percent_b', 'Bollinger %B', 'Technical', 'ratio', 0,
           'Position within the Bollinger Bands; 0 is the lower band, 1 the upper band.'),
    Metric('cmf', 'Chaikin money flow', 'Technical', 'ratio', 1,
           'Volume-weighted accumulation over 20 days; above 0 signals buying pressure.'),
    Metric('atr_percent', 'ATR', 'Technical', 'pctpt', 0,
           'Average true range over 14 days as a share of the price.'),
    Metric('volume_ratio', 'Volume ratio', 'Technical', 'ratio', 0,
           "Today's volume relative to the 20-day average."),
    Metric('pct_from_52w_high', 'From 52-week high', 'Technical', 'pct', 0,
           'Distance of the price below its 52-week high.'),

    # Quality
    Metric('quality_score', 'Quality score', 'Quality', 'num', 1,
           'Composite of profitability, balance sheet strength, growth and PEG ratio, from 0 to 100.'),
    Metric('altman_z_score', 'Altman Z-score', 'Quality', 'ratio', 1,
           'Bankruptcy risk: above 2.99 safe, 1.81 to 2.99 grey zone, below 1.81 distress. '
           'Not computed for financials, real estate and utilities, whose balance sheets the model was not built for.'),
    Metric('z_score_zone', 'Z-score zone', 'Quality', 'label', 0,
           'Safe, grey or distress zone of the Altman Z-score.'),

    # Analysts
    Metric('analyst_upside', 'Analyst upside', 'Analysts', 'pct', 1,
           'Mean analyst price target relative to the current price.'),
    Metric('target_low_price', 'Lowest price target', 'Analysts', 'price', 0,
           'Lowest analyst price target.'),
    Metric('target_mean_price', 'Mean price target', 'Analysts', 'price', 0,
           'Mean analyst price target.'),
    Metric('target_high_price', 'Highest price target', 'Analysts', 'price', 0,
           'Highest analyst price target.'),
    Metric('recommendation_mean', 'Analyst rating', 'Analysts', 'ratio', -1,
           'Consensus recommendation from 1 (strong buy) to 5 (sell).'),
    Metric('number_of_analyst_opinions', 'Analysts covering', 'Analysts', 'int', 0,
           'Number of analysts behind the consensus.'),
    Metric('short_percent_of_float', 'Short interest', 'Analysts', 'pct', 0,
           'Shares sold short as a share of the float.'),
    Metric('held_percent_institutions', 'Institutional ownership', 'Analysts', 'pct', 0,
           'Share of shares held by institutions.'),

    # Ratings
    Metric('valuation_category', 'Valuation', 'Ratings', 'label', 0,
           'Valuation rating bucket: the universe split into quintiles of the valuation score.'),
    Metric('valuation_rating', 'Valuation rating', 'Ratings', 'int', -1,
           '1 strongly undervalued to 5 strongly overvalued.'),
    Metric('valuation_score', 'Valuation score', 'Ratings', 'ratio', -1,
           'Weighted sector-relative forward P/E, P/B, debt/equity, inverse ROE, FCF yield and inverse margin; '
           'lower is cheaper relative to sector peers.'),
    Metric('performance_category', 'Performance', 'Ratings', 'label', 0,
           'Performance rating bucket: the universe split into quintiles of the performance score.'),
    Metric('performance_rating', 'Performance rating', 'Ratings', 'int', -1,
           '1 strong outperformer to 5 strong underperformer.'),
    Metric('performance_score', 'Performance score', 'Ratings', 'ratio', -1,
           'Weighted excess return, revenue growth, ROE and momentum; lower is better.'),
    Metric('combined_score', 'Combined rating', 'Ratings', 'ratio', -1,
           'Average of the valuation and performance ratings, from 1 (best) to 5 (worst).'),
]

IDENTITY_COLUMNS = ['ticker', 'name', 'sector', 'industry', 'index']

# Market value of each listing, for weights and totals (not shown as a metric)
WEIGHT_COLUMN = 'listing_cap'

BENCHMARKS = ['SPY', 'QQQ']


# =============================================================================
# JSON HELPERS
# =============================================================================

def _number(value, digits=6):
    """JSON-safe number rounded to significant digits, None when missing"""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    value = float(f'{value:.{digits}g}')
    return int(value) if value.is_integer() else value


def _text(value):
    """JSON-safe string, None when missing"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return str(value)


def _write_json(payload, path):
    with open(path, 'w') as f:
        json.dump(payload, f, separators=(',', ':'), allow_nan=False)
    print(f"Dashboard data saved to: {path} ({os.path.getsize(path) / 1024:.0f} KB)")


# =============================================================================
# STOCKS
# =============================================================================

def listing_caps(df):
    """
    Market value of each listed share class

    Yahoo reports the whole company's market cap on every class of a
    dual-class company (GOOG and GOOGL, FOX and FOXA), so summing market_cap
    counts such companies twice. Split the company value across its listings
    in proportion to each listing's own shares times price.
    """
    caps = df['market_cap'].astype(float)
    if 'name' not in df:
        return caps
    named = df[df['name'].fillna('') != '']
    for _, listings in named.groupby('name'):
        if len(listings) < 2:
            continue
        own = (listings['shares_outstanding'] * listings['current_price']
               if 'shares_outstanding' in listings else pd.Series(np.nan, index=listings.index))
        share = own / own.sum() if own.notna().all() and own.sum() > 0 else 1 / len(listings)
        caps.loc[listings.index] = listings['market_cap'].max() * share
    return caps


def add_derived_metrics(df):
    """Add the dashboard metrics that are simple ratios of fetched fields"""
    df = df.copy()
    df[WEIGHT_COLUMN] = listing_caps(df)

    if 'sharpe_ratio' not in df.columns and 'sharpe_approx' in df.columns:
        df['sharpe_ratio'] = df['sharpe_approx']

    if {'target_mean_price', 'current_price'} <= set(df.columns):
        df['analyst_upside'] = df['target_mean_price'] / df['current_price'] - 1

    if {'fifty_two_week_high', 'current_price'} <= set(df.columns):
        df['pct_from_52w_high'] = df['current_price'] / df['fifty_two_week_high'] - 1

    return df


def build_stock_table(df):
    """Stocks as a compact column/row table, with the catalog of included metrics"""
    df = add_derived_metrics(df).replace([np.inf, -np.inf], np.nan)
    labels = [m.key for m in METRICS if m.fmt == 'label' and m.key in df.columns]
    df[labels] = df[labels].replace('Unknown', np.nan)

    metrics = [m for m in METRICS if m.key in df.columns and df[m.key].notna().any()]
    identity = [c for c in IDENTITY_COLUMNS if c in df.columns]
    columns = identity + [WEIGHT_COLUMN] + [m.key for m in metrics]

    text_columns = set(identity) | {m.key for m in metrics if m.fmt == 'label'}
    rows = [
        [_text(row[c]) if c in text_columns else _number(row[c]) for c in columns]
        for _, row in df[columns].iterrows()
    ]

    catalog = [m._asdict() for m in metrics]
    return catalog, {'columns': columns, 'rows': rows}


# =============================================================================
# PRICE HISTORY
# =============================================================================

def _closes(price_histories, tickers):
    """Daily closes per ticker in one frame indexed by trading date"""
    series = {}
    for ticker in tickers:
        history = price_histories.get(ticker)
        if history is None or len(history) == 0:
            continue
        close = history['Close'].copy()
        close.index = pd.DatetimeIndex(close.index).tz_localize(None).normalize()
        series[ticker] = close[~close.index.duplicated(keep='last')]
    return pd.DataFrame(series).sort_index()


def _index_level(daily_returns):
    """Price index starting at 100 from a series of daily returns"""
    return 100 * (1 + daily_returns.fillna(0)).cumprod()


def sector_indices(closes, df):
    """
    Cap-weighted and equal-weighted daily price index per sector

    The cap-weighted index holds today's share count of every listing
    (listing market value / price), so each day's return is weighted by the
    previous day's market value; stocks enter once they have a price.
    """
    returns = closes.pct_change(fill_method=None)
    stocks = df.set_index('ticker')
    shares = listing_caps(stocks) / stocks['current_price']
    values = closes.mul(shares.reindex(closes.columns), axis=1).shift(1)

    indices = {}
    for sector, tickers in df.groupby('sector')['ticker']:
        cols = [t for t in tickers if t in closes.columns]
        if not cols:
            continue
        r, w = returns[cols], values[cols]
        valid = r.notna() & w.notna()
        cap_weighted = (r.where(valid) * w.where(valid)).sum(axis=1) / w.where(valid).sum(axis=1)
        indices[sector] = {
            'cap': _index_level(cap_weighted),
            'equal': _index_level(r.mean(axis=1)),
        }
    return indices


def build_history(df, price_histories, benchmark_data):
    """Daily sector and benchmark indices on the benchmark's trading calendar"""
    closes = _closes(price_histories, df['ticker'])
    if closes.empty:
        return None

    benchmarks = _closes(benchmark_data or {}, BENCHMARKS)
    calendar = benchmarks.index if not benchmarks.empty else closes.index
    closes = closes.reindex(calendar)

    def series(values):
        return [_number(v, 7) for v in values.reindex(calendar)]

    return {
        'dates': [d.strftime('%Y-%m-%d') for d in calendar],
        'benchmarks': {
            name: series(_index_level(benchmarks[name].pct_change(fill_method=None)))
            for name in benchmarks.columns
        },
        'sectors': {
            sector: {kind: series(level) for kind, level in levels.items()}
            for sector, levels in sector_indices(closes, df).items()
        },
    }


def build_weekly_prices(df, price_histories):
    """Weekly (Friday) closes per stock"""
    closes = _closes(price_histories, df['ticker'])
    if closes.empty:
        return None
    weekly = closes.resample('W-FRI').last()
    return {
        'dates': [d.strftime('%Y-%m-%d') for d in weekly.index],
        'prices': {
            ticker: [_number(v) for v in weekly[ticker]]
            for ticker in weekly.columns
        },
    }


# =============================================================================
# MODELS
# =============================================================================

def summarize_ols(model, target='excess_return'):
    """
    Fit statistics and coefficients of the cross-sectional OLS model

    Besides the raw coefficient, each factor carries its standardised
    effect: the change in the target for a one standard deviation move in
    the factor, which makes factors of different scale comparable.
    """
    if model is None:
        return None

    exog = pd.DataFrame(model.model.exog, columns=model.model.exog_names)
    conf_int = model.conf_int()
    coefficients = []
    for term in model.params.index:
        if term == 'const':
            continue
        sd = exog[term].std()
        coefficients.append({
            'term': term,
            'coef': _number(model.params[term]),
            'p': _number(model.pvalues[term]),
            'effect': _number(model.params[term] * sd),
            'effect_ci': [_number(conf_int.loc[term, 0] * sd), _number(conf_int.loc[term, 1] * sd)],
        })

    return {
        'target': target,
        'n': int(model.nobs),
        'r2': _number(model.rsquared),
        'adj_r2': _number(model.rsquared_adj),
        'f_pvalue': _number(model.f_pvalue),
        'coefficients': coefficients,
    }


def summarize_ml(df, ml_results, target='1y_return'):
    """Out-of-sample scores of the ML models and their feature importance"""
    if not ml_results:
        return None

    _, features = prepare_regression_data(df, target)
    importance = get_feature_importance(ml_results, features).drop(columns='average')
    # Normalise each model's importances to shares so linear and tree models average fairly
    share = (importance.abs() / importance.abs().sum()).mean(axis=1).sort_values(ascending=False)

    return {
        'target': target,
        'models': [
            {
                'name': name,
                'r2': _number(result['r2']),
                'rmse': _number(result['rmse']),
                'mae': _number(result['mae']),
                'cv_r2': _number(result['cv_r2_mean']),
                'cv_r2_std': _number(result['cv_r2_std']),
            }
            for name, result in sorted(ml_results.items(), key=lambda kv: -kv[1]['r2'])
        ],
        'importance': [{'feature': f, 'share': _number(v)} for f, v in share.items()],
    }


def summarize_sector_models(sector_models):
    """Fit and significant factors of the per-sector OLS models"""
    return [
        {
            'sector': sector,
            'n': int(data['n_obs']),
            'r2': _number(data['r2']),
            'adj_r2': _number(data['adj_r2']),
            'factors': [name for name, _, _ in data['significant_factors']],
        }
        for sector, data in sorted((sector_models or {}).items())
    ]


# =============================================================================
# EXPORT
# =============================================================================

def export_dashboard_data(df, output_dir, price_histories=None, benchmark_data=None,
                          ols_model=None, sector_models=None, ml_results=None,
                          demo_mode=False, universe_size=None):
    """
    Write dashboard.json (and prices.json when price history is available)

    Args:
        df: analysed stocks, one row per ticker
        output_dir: directory the dashboard reads its data from
        price_histories: {ticker: OHLCV DataFrame}
        benchmark_data: {symbol: OHLCV DataFrame}, e.g. from fetch_market_data()
        ols_model, sector_models, ml_results: outputs of generate_regression_report()
        demo_mode: whether df holds simulated data
        universe_size: number of tickers the analysis attempted
    """
    os.makedirs(output_dir, exist_ok=True)
    price_histories = price_histories or {}

    catalog, stocks = build_stock_table(df)
    history = build_history(df, price_histories, benchmark_data) if price_histories else None
    generated_at = datetime.now(timezone.utc)

    payload = {
        'meta': {
            'schema': SCHEMA_VERSION,
            'generated_at': generated_at.isoformat(timespec='seconds'),
            'as_of': history['dates'][-1] if history else generated_at.strftime('%Y-%m-%d'),
            'mode': 'demo' if demo_mode else 'live',
            'source': 'Simulated demo data' if demo_mode else 'Yahoo Finance via yfinance',
            'universe': {
                'name': 'S&P 500 + Nasdaq-100',
                'size': int(universe_size or len(df)),
                'analyzed': int(len(df)),
            },
            'benchmark': 'SPY',
            'risk_free_rate': 0.04,
        },
        'metrics': catalog,
        'stocks': stocks,
        'history': history,
        'models': {
            'ols': summarize_ols(ols_model),
            'ml': summarize_ml(df, ml_results),
            'sectors': summarize_sector_models(sector_models),
        },
    }
    _write_json(payload, os.path.join(output_dir, 'dashboard.json'))

    prices_path = os.path.join(output_dir, 'prices.json')
    prices = build_weekly_prices(df, price_histories) if price_histories else None
    if prices:
        _write_json(prices, prices_path)
    elif os.path.exists(prices_path):
        # Never leave weekly prices of an earlier run next to fresh data
        os.remove(prices_path)
