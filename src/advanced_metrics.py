"""
Advanced Metrics Module
Comprehensive metrics for stock analysis including:
- Performance metrics (Sharpe, Sortino, Calmar, Alpha, Beta)
- Technical indicators (RSI, Bollinger Bands, MACD)
- Composite scores (Altman Z-Score, Piotroski F-Score)
- Sector-relative metrics
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# PRICE & PERFORMANCE METRICS
# =============================================================================

def calculate_cumulative_return(prices):
    """Calculate cumulative return"""
    if len(prices) < 2:
        return np.nan
    return (prices.iloc[-1] / prices.iloc[0]) - 1


def calculate_annualized_return(prices, trading_days=252):
    """Calculate annualized return"""
    if len(prices) < 2:
        return np.nan
    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
    n_days = len(prices)
    years = n_days / trading_days
    if years <= 0:
        return np.nan
    return (1 + total_return) ** (1 / years) - 1


def calculate_volatility(returns, trading_days=252):
    """Calculate annualized volatility"""
    if len(returns) < 2:
        return np.nan
    return returns.std() * np.sqrt(trading_days)


def calculate_max_drawdown(prices):
    """Calculate maximum drawdown and recovery time"""
    if len(prices) < 2:
        return np.nan, np.nan, np.nan

    # Calculate running maximum
    rolling_max = prices.expanding().max()
    drawdowns = prices / rolling_max - 1

    max_dd = drawdowns.min()
    max_dd_idx = drawdowns.idxmin()

    # Find peak before max drawdown
    peak_idx = prices[:max_dd_idx].idxmax() if max_dd_idx is not None else None

    # Calculate recovery time
    recovery_time = np.nan
    if max_dd_idx is not None and peak_idx is not None:
        peak_value = prices[peak_idx]
        after_trough = prices[max_dd_idx:]
        recovered = after_trough[after_trough >= peak_value]
        if len(recovered) > 0:
            recovery_idx = recovered.index[0]
            recovery_time = len(prices[max_dd_idx:recovery_idx])

    return max_dd, peak_idx, recovery_time


def calculate_sharpe_ratio(returns, risk_free_rate=0.04, trading_days=252):
    """Calculate Sharpe Ratio"""
    if len(returns) < 2 or returns.std() == 0:
        return np.nan
    excess_returns = returns - risk_free_rate / trading_days
    return (excess_returns.mean() * trading_days) / (returns.std() * np.sqrt(trading_days))


def calculate_sortino_ratio(returns, risk_free_rate=0.04, trading_days=252):
    """Calculate Sortino Ratio (downside risk adjusted)"""
    if len(returns) < 2:
        return np.nan
    excess_returns = returns - risk_free_rate / trading_days
    downside_returns = returns[returns < 0]
    if len(downside_returns) < 2 or downside_returns.std() == 0:
        return np.nan
    downside_std = downside_returns.std() * np.sqrt(trading_days)
    return (excess_returns.mean() * trading_days) / downside_std


def calculate_calmar_ratio(returns, prices, trading_days=252):
    """Calculate Calmar Ratio (return / max drawdown)"""
    ann_return = calculate_annualized_return(prices, trading_days)
    max_dd, _, _ = calculate_max_drawdown(prices)
    if max_dd is None or max_dd == 0:
        return np.nan
    return ann_return / abs(max_dd)


def calculate_alpha_beta(stock_returns, market_returns, risk_free_rate=0.04, trading_days=252):
    """Calculate Alpha and Beta vs benchmark"""
    if len(stock_returns) < 10 or len(market_returns) < 10:
        return np.nan, np.nan

    # Align returns
    aligned = pd.concat([stock_returns, market_returns], axis=1, join='inner')
    if len(aligned) < 10:
        return np.nan, np.nan

    stock_ret = aligned.iloc[:, 0].values
    market_ret = aligned.iloc[:, 1].values

    # Calculate beta (slope) and alpha (intercept)
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(market_ret, stock_ret)
        beta = slope
        # Alpha = stock return - (risk free + beta * market excess return)
        alpha = (np.mean(stock_ret) * trading_days) - (risk_free_rate + beta * (np.mean(market_ret) * trading_days - risk_free_rate))
        return alpha, beta
    except:
        return np.nan, np.nan


def calculate_tracking_error(stock_returns, benchmark_returns, trading_days=252):
    """Calculate tracking error (std of excess returns)"""
    aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner')
    if len(aligned) < 10:
        return np.nan
    excess = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    return excess.std() * np.sqrt(trading_days)


def calculate_information_ratio(stock_returns, benchmark_returns, trading_days=252):
    """Calculate Information Ratio"""
    aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner')
    if len(aligned) < 10:
        return np.nan
    excess = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    tracking_error = excess.std() * np.sqrt(trading_days)
    if tracking_error == 0:
        return np.nan
    return (excess.mean() * trading_days) / tracking_error


def calculate_capture_ratios(stock_returns, benchmark_returns):
    """Calculate Up/Down Capture Ratios"""
    aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner')
    if len(aligned) < 20:
        return np.nan, np.nan

    stock_ret = aligned.iloc[:, 0]
    bench_ret = aligned.iloc[:, 1]

    # Up capture: performance when benchmark is up
    up_days = bench_ret > 0
    if up_days.sum() < 5:
        up_capture = np.nan
    else:
        up_capture = stock_ret[up_days].mean() / bench_ret[up_days].mean() * 100

    # Down capture: performance when benchmark is down
    down_days = bench_ret < 0
    if down_days.sum() < 5:
        down_capture = np.nan
    else:
        down_capture = stock_ret[down_days].mean() / bench_ret[down_days].mean() * 100

    return up_capture, down_capture


# =============================================================================
# FUNDAMENTAL METRICS - PROFITABILITY
# =============================================================================

def calculate_roic(net_income, total_debt, total_equity, cash):
    """Calculate Return on Invested Capital"""
    invested_capital = total_debt + total_equity - cash
    if invested_capital <= 0:
        return np.nan
    return net_income / invested_capital


def calculate_ebitda_margin(ebitda, revenue):
    """Calculate EBITDA Margin"""
    if revenue <= 0:
        return np.nan
    return ebitda / revenue


# =============================================================================
# VALUATION MULTIPLES
# =============================================================================

def calculate_shiller_cape(prices, earnings_history, years=10):
    """
    Calculate Shiller CAPE (Cyclically Adjusted P/E)
    Uses average of inflation-adjusted earnings over 10 years
    """
    if len(earnings_history) < years:
        return np.nan
    avg_earnings = earnings_history.tail(years * 4).mean()  # Quarterly
    if avg_earnings <= 0:
        return np.nan
    current_price = prices.iloc[-1] if isinstance(prices, pd.Series) else prices
    return current_price / avg_earnings


def calculate_pcf_ratio(price, operating_cashflow, shares_outstanding):
    """Calculate Price to Cash Flow ratio"""
    if shares_outstanding <= 0 or operating_cashflow <= 0:
        return np.nan
    cashflow_per_share = operating_cashflow / shares_outstanding
    return price / cashflow_per_share


# =============================================================================
# GROWTH METRICS
# =============================================================================

def calculate_cagr(start_value, end_value, years):
    """Calculate Compound Annual Growth Rate"""
    if start_value <= 0 or years <= 0:
        return np.nan
    return (end_value / start_value) ** (1 / years) - 1


def calculate_growth_rates(values, periods=['yoy', 'qoq']):
    """Calculate various growth rates"""
    results = {}
    if len(values) >= 4:
        results['qoq'] = (values.iloc[-1] / values.iloc[-2] - 1) if values.iloc[-2] != 0 else np.nan
    if len(values) >= 5:
        results['yoy'] = (values.iloc[-1] / values.iloc[-5] - 1) if values.iloc[-5] != 0 else np.nan
    if len(values) >= 12:
        results['cagr_3y'] = calculate_cagr(values.iloc[-12], values.iloc[-1], 3)
    return results


# =============================================================================
# BALANCE SHEET & FINANCIAL STABILITY
# =============================================================================

def calculate_quick_ratio(current_assets, inventory, current_liabilities):
    """Calculate Quick Ratio (Acid Test)"""
    if current_liabilities <= 0:
        return np.nan
    return (current_assets - inventory) / current_liabilities


def calculate_cash_ratio(cash, current_liabilities):
    """Calculate Cash Ratio"""
    if current_liabilities <= 0:
        return np.nan
    return cash / current_liabilities


def calculate_interest_coverage(ebit, interest_expense):
    """Calculate Interest Coverage Ratio"""
    if interest_expense <= 0:
        return np.nan
    return ebit / interest_expense


def calculate_net_debt_to_ebitda(total_debt, cash, ebitda):
    """Calculate Net Debt to EBITDA"""
    if ebitda <= 0:
        return np.nan
    net_debt = total_debt - cash
    return net_debt / ebitda


# =============================================================================
# OPERATIONAL EFFICIENCY
# =============================================================================

def calculate_asset_turnover(revenue, total_assets):
    """Calculate Asset Turnover Ratio"""
    if total_assets <= 0:
        return np.nan
    return revenue / total_assets


def calculate_inventory_turnover(cogs, inventory):
    """Calculate Inventory Turnover"""
    if inventory <= 0:
        return np.nan
    return cogs / inventory


def calculate_receivables_turnover(revenue, receivables):
    """Calculate Receivables Turnover"""
    if receivables <= 0:
        return np.nan
    return revenue / receivables


def calculate_operating_cycle(inventory_turnover, receivables_turnover):
    """Calculate Operating Cycle (days)"""
    if inventory_turnover <= 0 or receivables_turnover <= 0:
        return np.nan
    days_inventory = 365 / inventory_turnover
    days_receivables = 365 / receivables_turnover
    return days_inventory + days_receivables


# =============================================================================
# COMPOSITE QUALITY SCORES
# =============================================================================

def calculate_altman_z_score(working_capital, total_assets, retained_earnings,
                              ebit, market_cap, total_liabilities, revenue):
    """
    Calculate Altman Z-Score (Bankruptcy Predictor)
    Z > 2.99: Safe Zone
    1.81 < Z < 2.99: Grey Zone
    Z < 1.81: Distress Zone
    """
    if total_assets <= 0 or total_liabilities <= 0:
        return np.nan

    A = working_capital / total_assets
    B = retained_earnings / total_assets
    C = ebit / total_assets
    D = market_cap / total_liabilities
    E = revenue / total_assets

    z_score = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E
    return z_score


def calculate_piotroski_f_score(data):
    """
    Calculate Piotroski F-Score (Financial Health: 0-9)
    Higher is better

    Profitability (4 points):
    - Positive ROA
    - Positive Operating Cash Flow
    - ROA improvement
    - Cash flow > Net Income (Accruals)

    Leverage/Liquidity (3 points):
    - Decreased leverage (D/E)
    - Increased current ratio
    - No new shares issued

    Operating Efficiency (2 points):
    - Improved gross margin
    - Improved asset turnover
    """
    score = 0

    # Profitability
    if data.get('roa', 0) > 0:
        score += 1
    if data.get('operating_cashflow', 0) > 0:
        score += 1
    if data.get('roa_change', 0) > 0:
        score += 1
    if data.get('operating_cashflow', 0) > data.get('net_income', 0):
        score += 1

    # Leverage/Liquidity
    if data.get('debt_to_equity_change', 0) < 0:
        score += 1
    if data.get('current_ratio_change', 0) > 0:
        score += 1
    if data.get('shares_change', 0) <= 0:
        score += 1

    # Operating Efficiency
    if data.get('gross_margin_change', 0) > 0:
        score += 1
    if data.get('asset_turnover_change', 0) > 0:
        score += 1

    return score


def calculate_beneish_m_score(data):
    """
    Calculate Beneish M-Score (Earnings Manipulation Risk)
    M > -1.78 indicates higher probability of manipulation

    Variables:
    - DSRI: Days Sales in Receivables Index
    - GMI: Gross Margin Index
    - AQI: Asset Quality Index
    - SGI: Sales Growth Index
    - DEPI: Depreciation Index
    - SGAI: SG&A Index
    - TATA: Total Accruals to Total Assets
    - LVGI: Leverage Index
    """
    try:
        dsri = data.get('dsri', 1)
        gmi = data.get('gmi', 1)
        aqi = data.get('aqi', 1)
        sgi = data.get('sgi', 1)
        depi = data.get('depi', 1)
        sgai = data.get('sgai', 1)
        tata = data.get('tata', 0)
        lvgi = data.get('lvgi', 1)

        m_score = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi +
                   0.892 * sgi + 0.115 * depi - 0.172 * sgai +
                   4.679 * tata - 0.327 * lvgi)

        return m_score
    except:
        return np.nan


def calculate_composite_quality_score(data):
    """
    Calculate Composite Quality Score (proprietary)
    Combines multiple factors into a single quality metric (0-100)
    """
    score = 50  # Base score

    # Profitability factors (+/- up to 15)
    if pd.notna(data.get('roe')):
        score += min(max(data['roe'] * 50, -15), 15)
    if pd.notna(data.get('profit_margin')):
        score += min(max(data['profit_margin'] * 30, -10), 10)

    # Financial strength (+/- up to 15)
    if pd.notna(data.get('current_ratio')):
        if data['current_ratio'] > 2:
            score += 5
        elif data['current_ratio'] > 1.5:
            score += 3
        elif data['current_ratio'] < 1:
            score -= 5

    if pd.notna(data.get('debt_to_equity')):
        if data['debt_to_equity'] < 50:
            score += 5
        elif data['debt_to_equity'] > 200:
            score -= 10

    # Growth (+/- up to 10)
    if pd.notna(data.get('revenue_growth')):
        score += min(max(data['revenue_growth'] * 20, -10), 10)

    # Valuation (+/- up to 10)
    if pd.notna(data.get('peg_ratio')):
        if data['peg_ratio'] < 1:
            score += 5
        elif data['peg_ratio'] > 3:
            score -= 5

    return max(0, min(100, score))


# =============================================================================
# SECTOR-RELATIVE METRICS
# =============================================================================

def calculate_percentile_rank(value, sector_values):
    """Calculate percentile rank within sector"""
    if pd.isna(value) or len(sector_values.dropna()) < 3:
        return np.nan
    return stats.percentileofscore(sector_values.dropna(), value)


def calculate_sector_relative_metrics(stock_data, sector_data):
    """Calculate all sector-relative metrics"""
    relatives = {}

    metrics = ['forward_pe', 'price_to_book', 'roe', 'profit_margin',
               'revenue_growth', 'debt_to_equity']

    for metric in metrics:
        if metric in stock_data and metric in sector_data.columns:
            stock_val = stock_data[metric]
            sector_vals = sector_data[metric]

            if pd.notna(stock_val) and len(sector_vals.dropna()) > 0:
                relatives[f'{metric}_percentile'] = calculate_percentile_rank(stock_val, sector_vals)
                relatives[f'{metric}_vs_sector_median'] = stock_val / sector_vals.median() if sector_vals.median() != 0 else np.nan

    return relatives


# =============================================================================
# INDUSTRY-SPECIFIC METRICS
# =============================================================================

def calculate_tech_metrics(data):
    """Calculate tech-specific metrics"""
    metrics = {}

    # R&D intensity
    if pd.notna(data.get('rd_expense')) and pd.notna(data.get('total_revenue')):
        if data['total_revenue'] > 0:
            metrics['rd_to_sales'] = data['rd_expense'] / data['total_revenue']

    # Rule of 40 (for SaaS) - revenue growth + profit margin should be > 40%
    if pd.notna(data.get('revenue_growth')) and pd.notna(data.get('profit_margin')):
        metrics['rule_of_40'] = data['revenue_growth'] + data['profit_margin']

    return metrics


def calculate_financial_metrics(data):
    """Calculate financial sector specific metrics"""
    metrics = {}

    # Net Interest Margin
    if pd.notna(data.get('net_interest_income')) and pd.notna(data.get('average_earning_assets')):
        if data['average_earning_assets'] > 0:
            metrics['net_interest_margin'] = data['net_interest_income'] / data['average_earning_assets']

    return metrics


def calculate_energy_metrics(data):
    """Calculate energy sector specific metrics"""
    metrics = {}

    # These would typically come from specialized data sources
    # Placeholder for structure

    return metrics


# =============================================================================
# MACRO SENSITIVITY
# =============================================================================

def calculate_factor_beta(stock_returns, factor_returns):
    """Calculate beta to a specific factor (rates, USD, oil, VIX)"""
    aligned = pd.concat([stock_returns, factor_returns], axis=1, join='inner')
    if len(aligned) < 30:
        return np.nan

    try:
        slope, _, _, _, _ = stats.linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])
        return slope
    except:
        return np.nan


# =============================================================================
# COMPREHENSIVE METRICS CALCULATOR
# =============================================================================

def calculate_all_performance_metrics(prices, returns, benchmark_prices=None, benchmark_returns=None):
    """Calculate all performance metrics for a stock"""
    metrics = {}

    # Basic performance
    metrics['cumulative_return'] = calculate_cumulative_return(prices)
    metrics['annualized_return'] = calculate_annualized_return(prices)
    metrics['volatility'] = calculate_volatility(returns)

    # Drawdown
    max_dd, _, recovery_time = calculate_max_drawdown(prices)
    metrics['max_drawdown'] = max_dd
    metrics['recovery_time_days'] = recovery_time

    # Risk-adjusted returns
    metrics['sharpe_ratio'] = calculate_sharpe_ratio(returns)
    metrics['sortino_ratio'] = calculate_sortino_ratio(returns)
    metrics['calmar_ratio'] = calculate_calmar_ratio(returns, prices)

    # Relative performance (if benchmark provided)
    if benchmark_returns is not None:
        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)
        metrics['alpha'] = alpha
        metrics['beta'] = beta
        metrics['tracking_error'] = calculate_tracking_error(returns, benchmark_returns)
        metrics['information_ratio'] = calculate_information_ratio(returns, benchmark_returns)
        up_cap, down_cap = calculate_capture_ratios(returns, benchmark_returns)
        metrics['up_capture'] = up_cap
        metrics['down_capture'] = down_cap

    return metrics


def calculate_all_fundamental_metrics(stock_info):
    """Calculate all fundamental metrics from stock info"""
    metrics = {}

    # Direct from info
    direct_metrics = [
        'market_cap', 'forward_pe', 'trailing_pe', 'peg_ratio', 'price_to_book',
        'price_to_sales', 'ev_to_ebitda', 'ev_to_revenue', 'profit_margin',
        'operating_margin', 'gross_margin', 'roe', 'roa', 'debt_to_equity',
        'current_ratio', 'quick_ratio', 'revenue_growth', 'earnings_growth',
        'free_cashflow', 'operating_cashflow', 'dividend_yield', 'beta'
    ]

    for metric in direct_metrics:
        metrics[metric] = stock_info.get(metric, np.nan)

    # Calculated metrics
    if pd.notna(stock_info.get('net_income')) and pd.notna(stock_info.get('total_debt')):
        metrics['roic'] = calculate_roic(
            stock_info.get('net_income', 0),
            stock_info.get('total_debt', 0),
            stock_info.get('total_equity', stock_info.get('market_cap', 0)),
            stock_info.get('total_cash', 0)
        )

    if pd.notna(stock_info.get('ebitda')) and pd.notna(stock_info.get('total_revenue')):
        metrics['ebitda_margin'] = calculate_ebitda_margin(
            stock_info.get('ebitda', 0),
            stock_info.get('total_revenue', 0)
        )

    # FCF Yield
    if pd.notna(stock_info.get('free_cashflow')) and pd.notna(stock_info.get('market_cap')):
        if stock_info['market_cap'] > 0:
            metrics['fcf_yield'] = stock_info['free_cashflow'] / stock_info['market_cap']

    # Net Debt to EBITDA
    if all(pd.notna(stock_info.get(k)) for k in ['total_debt', 'total_cash', 'ebitda']):
        metrics['net_debt_to_ebitda'] = calculate_net_debt_to_ebitda(
            stock_info['total_debt'],
            stock_info['total_cash'],
            stock_info['ebitda']
        )

    return metrics
