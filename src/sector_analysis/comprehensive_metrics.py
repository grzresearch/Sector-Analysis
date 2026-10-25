"""
Comprehensive Metrics Module
============================
Complete implementation of all stock analysis metrics including:

1. PRICE & PERFORMANCE METRICS
   - Absolute Performance (Cumulative Return, Annualized Return, Max Drawdown, etc.)
   - Relative Performance (Alpha, Beta, Tracking Error, Information Ratio, etc.)

2. FUNDAMENTAL VALUATION METRICS
   - Profitability (ROE, ROA, ROIC, Margins)
   - Valuation Multiples (P/E, P/B, P/S, EV/EBITDA, CAPE, etc.)

3. GROWTH METRICS
   - Revenue & Earnings Growth (YoY, QoQ, CAGR)
   - Future Growth Expectations (Estimates, PEG)

4. BALANCE SHEET & FINANCIAL STABILITY
   - Liquidity (Current Ratio, Quick Ratio, Cash Ratio)
   - Leverage (Debt/Equity, Debt/EBITDA, Interest Coverage)

5. OPERATIONAL EFFICIENCY
   - Asset Turnover, Inventory Turnover, Receivables Turnover

6. MARKET & SENTIMENT INDICATORS
   - Technical Indicators (RSI, MACD, Bollinger Bands)
   - Trading Activity (Volume, VWAP, Short Interest)

7. SECTOR-RELATIVE METRICS
   - Valuation Percentiles, Growth vs Sector

8. COMPOSITE QUALITY SCORES
   - Altman Z-Score, Piotroski F-Score, Beneish M-Score

9. MACRO SENSITIVITY
   - Beta to Interest Rates, USD, Oil, VIX

10. INDUSTRY-SPECIFIC METRICS
    - Tech (R&D/Sales, Rule of 40)
    - Financials (NIM, Tier 1 Ratio)
    - Energy (Reserve Replacement)
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# 1. PRICE & PERFORMANCE METRICS - ABSOLUTE
# =============================================================================

class PerformanceMetrics:
    """Calculate comprehensive performance metrics"""

    @staticmethod
    def cumulative_return(prices):
        """Calculate cumulative return"""
        if prices is None or len(prices) < 2:
            return np.nan
        return (prices.iloc[-1] / prices.iloc[0]) - 1

    @staticmethod
    def annualized_return(prices, trading_days=252):
        """Calculate annualized return"""
        if prices is None or len(prices) < 2:
            return np.nan
        total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
        n_days = len(prices)
        years = n_days / trading_days
        if years <= 0:
            return np.nan
        return (1 + total_return) ** (1 / years) - 1

    @staticmethod
    def max_drawdown(prices):
        """
        Calculate Maximum Drawdown and related metrics
        Returns: (max_dd, peak_date, trough_date, recovery_days)
        """
        if prices is None or len(prices) < 2:
            return np.nan, None, None, np.nan

        rolling_max = prices.expanding().max()
        drawdowns = prices / rolling_max - 1

        max_dd = drawdowns.min()
        trough_idx = drawdowns.idxmin()
        peak_idx = prices[:trough_idx].idxmax() if trough_idx is not None else None

        # Calculate recovery time
        recovery_days = np.nan
        if trough_idx is not None and peak_idx is not None:
            peak_value = prices[peak_idx]
            after_trough = prices[trough_idx:]
            recovered = after_trough[after_trough >= peak_value]
            if len(recovered) > 0:
                recovery_idx = recovered.index[0]
                recovery_days = len(prices[trough_idx:recovery_idx])

        return max_dd, peak_idx, trough_idx, recovery_days

    @staticmethod
    def volatility(returns, trading_days=252):
        """Calculate annualized volatility (standard deviation)"""
        if returns is None or len(returns) < 2:
            return np.nan
        return returns.std() * np.sqrt(trading_days)

    @staticmethod
    def downside_volatility(returns, threshold=0, trading_days=252):
        """Calculate downside volatility (for Sortino Ratio)"""
        if returns is None or len(returns) < 2:
            return np.nan
        downside = returns[returns < threshold]
        if len(downside) < 2:
            return np.nan
        return downside.std() * np.sqrt(trading_days)

    @staticmethod
    def sharpe_ratio(returns, risk_free_rate=0.04, trading_days=252):
        """
        Calculate Sharpe Ratio
        Sharpe = (Return - Risk-Free Rate) / Volatility
        """
        if returns is None or len(returns) < 2:
            return np.nan
        vol = returns.std() * np.sqrt(trading_days)
        if vol == 0:
            return np.nan
        excess_return = (returns.mean() * trading_days) - risk_free_rate
        return excess_return / vol

    @staticmethod
    def sortino_ratio(returns, risk_free_rate=0.04, trading_days=252):
        """
        Calculate Sortino Ratio
        Sortino = (Return - Risk-Free Rate) / Downside Volatility
        """
        if returns is None or len(returns) < 2:
            return np.nan
        downside_vol = PerformanceMetrics.downside_volatility(returns, 0, trading_days)
        if downside_vol == 0 or np.isnan(downside_vol):
            return np.nan
        excess_return = (returns.mean() * trading_days) - risk_free_rate
        return excess_return / downside_vol

    @staticmethod
    def calmar_ratio(prices, returns, trading_days=252):
        """
        Calculate Calmar Ratio
        Calmar = Annualized Return / |Max Drawdown|
        """
        ann_return = PerformanceMetrics.annualized_return(prices, trading_days)
        max_dd, _, _, _ = PerformanceMetrics.max_drawdown(prices)
        if max_dd == 0 or np.isnan(max_dd):
            return np.nan
        return ann_return / abs(max_dd)

    @staticmethod
    def omega_ratio(returns, threshold=0):
        """
        Calculate Omega Ratio
        Omega = Sum of returns above threshold / Sum of returns below threshold
        """
        if returns is None or len(returns) < 2:
            return np.nan
        above = returns[returns > threshold].sum()
        below = abs(returns[returns < threshold].sum())
        if below == 0:
            return np.nan
        return above / below

    @staticmethod
    def calculate_var(returns, confidence=0.95):
        """Calculate Value at Risk (VaR)"""
        if returns is None or len(returns) < 10:
            return np.nan
        return np.percentile(returns, (1 - confidence) * 100)

    @staticmethod
    def calculate_cvar(returns, confidence=0.95):
        """Calculate Conditional VaR (Expected Shortfall)"""
        if returns is None or len(returns) < 10:
            return np.nan
        var = PerformanceMetrics.calculate_var(returns, confidence)
        return returns[returns <= var].mean()


# =============================================================================
# 1. PRICE & PERFORMANCE METRICS - RELATIVE
# =============================================================================

class RelativePerformanceMetrics:
    """Calculate relative/benchmark-adjusted performance metrics"""

    @staticmethod
    def alpha_beta(stock_returns, benchmark_returns, risk_free_rate=0.04, trading_days=252):
        """
        Calculate Alpha and Beta vs benchmark
        Alpha = Excess return not explained by market movement
        Beta = Sensitivity to market movements
        """
        if stock_returns is None or benchmark_returns is None:
            return np.nan, np.nan

        aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner').dropna()
        if len(aligned) < 30:
            return np.nan, np.nan

        stock_ret = aligned.iloc[:, 0].values
        market_ret = aligned.iloc[:, 1].values

        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(market_ret, stock_ret)
            beta = slope
            # Jensen's Alpha
            alpha = (np.mean(stock_ret) * trading_days) - (
                risk_free_rate + beta * (np.mean(market_ret) * trading_days - risk_free_rate)
            )
            return alpha, beta
        except:
            return np.nan, np.nan

    @staticmethod
    def tracking_error(stock_returns, benchmark_returns, trading_days=252):
        """Calculate Tracking Error (standard deviation of excess returns)"""
        if stock_returns is None or benchmark_returns is None:
            return np.nan

        aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner').dropna()
        if len(aligned) < 30:
            return np.nan

        excess = aligned.iloc[:, 0] - aligned.iloc[:, 1]
        return excess.std() * np.sqrt(trading_days)

    @staticmethod
    def information_ratio(stock_returns, benchmark_returns, trading_days=252):
        """
        Calculate Information Ratio
        IR = Active Return / Tracking Error
        """
        if stock_returns is None or benchmark_returns is None:
            return np.nan

        aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner').dropna()
        if len(aligned) < 30:
            return np.nan

        excess = aligned.iloc[:, 0] - aligned.iloc[:, 1]
        tracking_err = excess.std() * np.sqrt(trading_days)
        if tracking_err == 0:
            return np.nan

        active_return = excess.mean() * trading_days
        return active_return / tracking_err

    @staticmethod
    def up_down_capture(stock_returns, benchmark_returns):
        """
        Calculate Up Capture and Down Capture Ratios
        Up Capture > 100: Outperforms in up markets
        Down Capture < 100: Loses less in down markets
        """
        if stock_returns is None or benchmark_returns is None:
            return np.nan, np.nan

        aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner').dropna()
        if len(aligned) < 30:
            return np.nan, np.nan

        stock_ret = aligned.iloc[:, 0]
        bench_ret = aligned.iloc[:, 1]

        # Up capture
        up_days = bench_ret > 0
        if up_days.sum() < 10:
            up_capture = np.nan
        else:
            up_capture = (stock_ret[up_days].mean() / bench_ret[up_days].mean()) * 100

        # Down capture
        down_days = bench_ret < 0
        if down_days.sum() < 10:
            down_capture = np.nan
        else:
            down_capture = (stock_ret[down_days].mean() / bench_ret[down_days].mean()) * 100

        return up_capture, down_capture

    @staticmethod
    def r_squared(stock_returns, benchmark_returns):
        """Calculate R-squared (coefficient of determination)"""
        if stock_returns is None or benchmark_returns is None:
            return np.nan

        aligned = pd.concat([stock_returns, benchmark_returns], axis=1, join='inner').dropna()
        if len(aligned) < 30:
            return np.nan

        correlation = aligned.corr().iloc[0, 1]
        return correlation ** 2


# =============================================================================
# 2. FUNDAMENTAL METRICS - PROFITABILITY
# =============================================================================

class ProfitabilityMetrics:
    """Calculate profitability metrics"""

    @staticmethod
    def gross_margin(gross_profit, revenue):
        """Gross Margin = Gross Profit / Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return gross_profit / revenue if gross_profit is not None else np.nan

    @staticmethod
    def operating_margin(operating_income, revenue):
        """Operating Margin = Operating Income / Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return operating_income / revenue if operating_income is not None else np.nan

    @staticmethod
    def net_margin(net_income, revenue):
        """Net Margin = Net Income / Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return net_income / revenue if net_income is not None else np.nan

    @staticmethod
    def ebitda_margin(ebitda, revenue):
        """EBITDA Margin = EBITDA / Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return ebitda / revenue if ebitda is not None else np.nan

    @staticmethod
    def roe(net_income, shareholders_equity):
        """Return on Equity = Net Income / Shareholders' Equity"""
        if shareholders_equity is None or shareholders_equity <= 0:
            return np.nan
        return net_income / shareholders_equity if net_income is not None else np.nan

    @staticmethod
    def roa(net_income, total_assets):
        """Return on Assets = Net Income / Total Assets"""
        if total_assets is None or total_assets <= 0:
            return np.nan
        return net_income / total_assets if net_income is not None else np.nan

    @staticmethod
    def roic(nopat, invested_capital):
        """
        Return on Invested Capital
        ROIC = NOPAT / Invested Capital
        Invested Capital = Total Debt + Equity - Cash
        """
        if invested_capital is None or invested_capital <= 0:
            return np.nan
        return nopat / invested_capital if nopat is not None else np.nan

    @staticmethod
    def calculate_roic_from_data(net_income, total_debt, total_equity, cash, tax_rate=0.25):
        """Calculate ROIC from individual components"""
        if any(x is None for x in [net_income, total_debt, total_equity]):
            return np.nan

        invested_capital = total_debt + total_equity - (cash or 0)
        if invested_capital <= 0:
            return np.nan

        # Approximate NOPAT
        nopat = net_income * (1 + tax_rate * 0.3)  # Simplified approximation
        return nopat / invested_capital

    @staticmethod
    def roce(ebit, capital_employed):
        """Return on Capital Employed = EBIT / Capital Employed"""
        if capital_employed is None or capital_employed <= 0:
            return np.nan
        return ebit / capital_employed if ebit is not None else np.nan


# =============================================================================
# 2. FUNDAMENTAL METRICS - VALUATION MULTIPLES
# =============================================================================

class ValuationMetrics:
    """Calculate valuation multiples"""

    @staticmethod
    def pe_ratio(price, eps):
        """Price-to-Earnings Ratio"""
        if eps is None or eps <= 0:
            return np.nan
        return price / eps if price is not None else np.nan

    @staticmethod
    def forward_pe(price, forward_eps):
        """Forward P/E using estimated EPS"""
        return ValuationMetrics.pe_ratio(price, forward_eps)

    @staticmethod
    def trailing_pe(price, trailing_eps):
        """Trailing P/E using historical EPS"""
        return ValuationMetrics.pe_ratio(price, trailing_eps)

    @staticmethod
    def shiller_cape(price, earnings_10y_avg, inflation_adj_factor=1.0):
        """
        Cyclically Adjusted P/E (Shiller CAPE)
        Uses 10-year average inflation-adjusted earnings
        """
        if earnings_10y_avg is None or earnings_10y_avg <= 0:
            return np.nan
        adj_earnings = earnings_10y_avg * inflation_adj_factor
        return price / adj_earnings if price is not None else np.nan

    @staticmethod
    def pb_ratio(price, book_value_per_share):
        """Price-to-Book Ratio"""
        if book_value_per_share is None or book_value_per_share <= 0:
            return np.nan
        return price / book_value_per_share if price is not None else np.nan

    @staticmethod
    def ps_ratio(market_cap, revenue):
        """Price-to-Sales Ratio"""
        if revenue is None or revenue <= 0:
            return np.nan
        return market_cap / revenue if market_cap is not None else np.nan

    @staticmethod
    def ev_to_ebitda(enterprise_value, ebitda):
        """EV/EBITDA"""
        if ebitda is None or ebitda <= 0:
            return np.nan
        return enterprise_value / ebitda if enterprise_value is not None else np.nan

    @staticmethod
    def ev_to_revenue(enterprise_value, revenue):
        """EV/Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return enterprise_value / revenue if enterprise_value is not None else np.nan

    @staticmethod
    def pcf_ratio(price, operating_cashflow_per_share):
        """Price-to-Cash Flow Ratio"""
        if operating_cashflow_per_share is None or operating_cashflow_per_share <= 0:
            return np.nan
        return price / operating_cashflow_per_share if price is not None else np.nan

    @staticmethod
    def fcf_yield(free_cashflow, market_cap):
        """Free Cash Flow Yield = FCF / Market Cap"""
        if market_cap is None or market_cap <= 0:
            return np.nan
        return free_cashflow / market_cap if free_cashflow is not None else np.nan

    @staticmethod
    def dividend_yield(dividend_per_share, price):
        """Dividend Yield = Annual Dividend / Price"""
        if price is None or price <= 0:
            return np.nan
        return dividend_per_share / price if dividend_per_share is not None else np.nan

    @staticmethod
    def peg_ratio(pe_ratio, earnings_growth_rate):
        """PEG Ratio = P/E / Earnings Growth Rate"""
        if earnings_growth_rate is None or earnings_growth_rate <= 0:
            return np.nan
        return pe_ratio / (earnings_growth_rate * 100) if pe_ratio is not None else np.nan


# =============================================================================
# 3. GROWTH METRICS
# =============================================================================

class GrowthMetrics:
    """Calculate growth metrics"""

    @staticmethod
    def yoy_growth(current, prior):
        """Year-over-Year Growth"""
        if prior is None or prior == 0:
            return np.nan
        return (current - prior) / abs(prior) if current is not None else np.nan

    @staticmethod
    def qoq_growth(current, prior):
        """Quarter-over-Quarter Growth"""
        return GrowthMetrics.yoy_growth(current, prior)

    @staticmethod
    def cagr(start_value, end_value, years):
        """
        Compound Annual Growth Rate
        CAGR = (End Value / Start Value)^(1/years) - 1
        """
        if start_value is None or start_value <= 0 or years <= 0:
            return np.nan
        return (end_value / start_value) ** (1 / years) - 1 if end_value is not None else np.nan

    @staticmethod
    def revenue_growth_rate(revenues_series):
        """Calculate revenue growth from series of revenues"""
        if revenues_series is None or len(revenues_series) < 2:
            return np.nan
        return GrowthMetrics.yoy_growth(revenues_series.iloc[-1], revenues_series.iloc[0])

    @staticmethod
    def eps_growth_rate(eps_series):
        """Calculate EPS growth from series of EPS"""
        if eps_series is None or len(eps_series) < 2:
            return np.nan
        return GrowthMetrics.yoy_growth(eps_series.iloc[-1], eps_series.iloc[0])

    @staticmethod
    def sustainable_growth_rate(roe, retention_ratio):
        """
        Sustainable Growth Rate = ROE * Retention Ratio
        Retention Ratio = 1 - Payout Ratio
        """
        if roe is None or retention_ratio is None:
            return np.nan
        return roe * retention_ratio


# =============================================================================
# 4. BALANCE SHEET & FINANCIAL STABILITY
# =============================================================================

class FinancialStabilityMetrics:
    """Calculate liquidity and leverage metrics"""

    # Liquidity Metrics
    @staticmethod
    def current_ratio(current_assets, current_liabilities):
        """Current Ratio = Current Assets / Current Liabilities"""
        if current_liabilities is None or current_liabilities <= 0:
            return np.nan
        return current_assets / current_liabilities if current_assets is not None else np.nan

    @staticmethod
    def quick_ratio(current_assets, inventory, current_liabilities):
        """Quick Ratio = (Current Assets - Inventory) / Current Liabilities"""
        if current_liabilities is None or current_liabilities <= 0:
            return np.nan
        if current_assets is None:
            return np.nan
        inv = inventory if inventory is not None else 0
        return (current_assets - inv) / current_liabilities

    @staticmethod
    def cash_ratio(cash, current_liabilities):
        """Cash Ratio = Cash / Current Liabilities"""
        if current_liabilities is None or current_liabilities <= 0:
            return np.nan
        return cash / current_liabilities if cash is not None else np.nan

    # Leverage Metrics
    @staticmethod
    def debt_to_equity(total_debt, shareholders_equity):
        """Debt-to-Equity Ratio"""
        if shareholders_equity is None or shareholders_equity <= 0:
            return np.nan
        return total_debt / shareholders_equity if total_debt is not None else np.nan

    @staticmethod
    def debt_to_assets(total_debt, total_assets):
        """Debt-to-Assets Ratio"""
        if total_assets is None or total_assets <= 0:
            return np.nan
        return total_debt / total_assets if total_debt is not None else np.nan

    @staticmethod
    def debt_to_ebitda(total_debt, ebitda):
        """Debt/EBITDA"""
        if ebitda is None or ebitda <= 0:
            return np.nan
        return total_debt / ebitda if total_debt is not None else np.nan

    @staticmethod
    def net_debt_to_ebitda(total_debt, cash, ebitda):
        """Net Debt/EBITDA = (Total Debt - Cash) / EBITDA"""
        if ebitda is None or ebitda <= 0:
            return np.nan
        if total_debt is None:
            return np.nan
        net_debt = total_debt - (cash or 0)
        return net_debt / ebitda

    @staticmethod
    def interest_coverage(ebit, interest_expense):
        """Interest Coverage Ratio = EBIT / Interest Expense"""
        if interest_expense is None or interest_expense <= 0:
            return np.nan
        return ebit / interest_expense if ebit is not None else np.nan

    @staticmethod
    def equity_multiplier(total_assets, shareholders_equity):
        """Equity Multiplier = Total Assets / Shareholders' Equity"""
        if shareholders_equity is None or shareholders_equity <= 0:
            return np.nan
        return total_assets / shareholders_equity if total_assets is not None else np.nan


# =============================================================================
# 5. OPERATIONAL EFFICIENCY
# =============================================================================

class EfficiencyMetrics:
    """Calculate operational efficiency metrics"""

    @staticmethod
    def asset_turnover(revenue, total_assets):
        """Asset Turnover = Revenue / Total Assets"""
        if total_assets is None or total_assets <= 0:
            return np.nan
        return revenue / total_assets if revenue is not None else np.nan

    @staticmethod
    def inventory_turnover(cogs, average_inventory):
        """Inventory Turnover = COGS / Average Inventory"""
        if average_inventory is None or average_inventory <= 0:
            return np.nan
        return cogs / average_inventory if cogs is not None else np.nan

    @staticmethod
    def days_inventory_outstanding(inventory_turnover):
        """Days Inventory Outstanding = 365 / Inventory Turnover"""
        if inventory_turnover is None or inventory_turnover <= 0:
            return np.nan
        return 365 / inventory_turnover

    @staticmethod
    def receivables_turnover(revenue, average_receivables):
        """Receivables Turnover = Revenue / Average Receivables"""
        if average_receivables is None or average_receivables <= 0:
            return np.nan
        return revenue / average_receivables if revenue is not None else np.nan

    @staticmethod
    def days_sales_outstanding(receivables_turnover):
        """Days Sales Outstanding = 365 / Receivables Turnover"""
        if receivables_turnover is None or receivables_turnover <= 0:
            return np.nan
        return 365 / receivables_turnover

    @staticmethod
    def payables_turnover(cogs, average_payables):
        """Payables Turnover = COGS / Average Payables"""
        if average_payables is None or average_payables <= 0:
            return np.nan
        return cogs / average_payables if cogs is not None else np.nan

    @staticmethod
    def days_payables_outstanding(payables_turnover):
        """Days Payables Outstanding = 365 / Payables Turnover"""
        if payables_turnover is None or payables_turnover <= 0:
            return np.nan
        return 365 / payables_turnover

    @staticmethod
    def cash_conversion_cycle(dio, dso, dpo):
        """
        Cash Conversion Cycle = DIO + DSO - DPO
        DIO = Days Inventory Outstanding
        DSO = Days Sales Outstanding
        DPO = Days Payables Outstanding
        """
        if any(x is None or np.isnan(x) for x in [dio, dso, dpo]):
            return np.nan
        return dio + dso - dpo

    @staticmethod
    def operating_cycle(dio, dso):
        """Operating Cycle = DIO + DSO"""
        if dio is None or dso is None:
            return np.nan
        return dio + dso


# =============================================================================
# 8. COMPOSITE QUALITY SCORES
# =============================================================================

class CompositeScores:
    """Calculate composite quality and risk scores"""

    @staticmethod
    def altman_z_score(working_capital, total_assets, retained_earnings,
                       ebit, market_cap, total_liabilities, revenue):
        """
        Altman Z-Score (Bankruptcy Predictor)
        Z > 2.99: Safe Zone
        1.81 < Z < 2.99: Grey Zone
        Z < 1.81: Distress Zone

        Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
        A = Working Capital / Total Assets
        B = Retained Earnings / Total Assets
        C = EBIT / Total Assets
        D = Market Cap / Total Liabilities
        E = Revenue / Total Assets
        """
        if total_assets is None or total_assets <= 0:
            return np.nan
        if total_liabilities is None or total_liabilities <= 0:
            return np.nan

        A = (working_capital or 0) / total_assets
        B = (retained_earnings or 0) / total_assets
        C = (ebit or 0) / total_assets
        D = (market_cap or 0) / total_liabilities
        E = (revenue or 0) / total_assets

        return 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E

    @staticmethod
    def interpret_z_score(z_score):
        """Interpret Altman Z-Score"""
        if z_score is None or np.isnan(z_score):
            return "Unknown"
        if z_score > 2.99:
            return "Safe Zone"
        elif z_score > 1.81:
            return "Grey Zone"
        else:
            return "Distress Zone"

    @staticmethod
    def piotroski_f_score(data):
        """
        Piotroski F-Score (Financial Health: 0-9)
        Higher is better

        Profitability (4 points):
        - Positive ROA
        - Positive Operating Cash Flow
        - ROA improvement (vs prior year)
        - Accrual Quality (CFO > Net Income)

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

    @staticmethod
    def interpret_f_score(f_score):
        """Interpret Piotroski F-Score"""
        if f_score is None or np.isnan(f_score):
            return "Unknown"
        if f_score >= 8:
            return "Strong"
        elif f_score >= 5:
            return "Average"
        else:
            return "Weak"

    @staticmethod
    def beneish_m_score(data):
        """
        Beneish M-Score (Earnings Manipulation Risk)
        M > -1.78: Higher probability of manipulation
        M < -1.78: Lower probability of manipulation

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
            dsri = data.get('dsri', 1.0)
            gmi = data.get('gmi', 1.0)
            aqi = data.get('aqi', 1.0)
            sgi = data.get('sgi', 1.0)
            depi = data.get('depi', 1.0)
            sgai = data.get('sgai', 1.0)
            tata = data.get('tata', 0.0)
            lvgi = data.get('lvgi', 1.0)

            m_score = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi +
                       0.892 * sgi + 0.115 * depi - 0.172 * sgai +
                       4.679 * tata - 0.327 * lvgi)

            return m_score
        except:
            return np.nan

    @staticmethod
    def interpret_m_score(m_score):
        """Interpret Beneish M-Score"""
        if m_score is None or np.isnan(m_score):
            return "Unknown"
        if m_score > -1.78:
            return "Higher Manipulation Risk"
        else:
            return "Lower Manipulation Risk"

    @staticmethod
    def quality_score(data):
        """
        Composite Quality Score (0-100)
        Combines multiple factors
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
# 9. MACRO SENSITIVITY
# =============================================================================

class MacroSensitivity:
    """Calculate sensitivity to macro factors"""

    @staticmethod
    def factor_beta(stock_returns, factor_returns):
        """Calculate beta to any factor (interest rates, USD, oil, VIX)"""
        if stock_returns is None or factor_returns is None:
            return np.nan

        aligned = pd.concat([stock_returns, factor_returns], axis=1, join='inner').dropna()
        if len(aligned) < 60:
            return np.nan

        try:
            slope, _, _, _, _ = stats.linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])
            return slope
        except:
            return np.nan

    @staticmethod
    def interest_rate_beta(stock_returns, bond_returns):
        """Beta to interest rates (using bond ETF like TLT as proxy)"""
        return MacroSensitivity.factor_beta(stock_returns, bond_returns)

    @staticmethod
    def usd_beta(stock_returns, usd_returns):
        """Beta to USD (using UUP ETF as proxy)"""
        return MacroSensitivity.factor_beta(stock_returns, usd_returns)

    @staticmethod
    def oil_beta(stock_returns, oil_returns):
        """Beta to oil prices (using USO ETF as proxy)"""
        return MacroSensitivity.factor_beta(stock_returns, oil_returns)

    @staticmethod
    def vix_beta(stock_returns, vix_returns):
        """Beta to VIX (volatility sensitivity)"""
        return MacroSensitivity.factor_beta(stock_returns, vix_returns)


# =============================================================================
# 10. INDUSTRY-SPECIFIC METRICS
# =============================================================================

class TechMetrics:
    """Technology sector specific metrics"""

    @staticmethod
    def rd_to_sales(rd_expense, revenue):
        """R&D Intensity = R&D Expense / Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return rd_expense / revenue if rd_expense is not None else np.nan

    @staticmethod
    def rule_of_40(revenue_growth, profit_margin):
        """
        Rule of 40 (for SaaS companies)
        Revenue Growth + Profit Margin should be > 40%
        """
        if revenue_growth is None or profit_margin is None:
            return np.nan
        return (revenue_growth + profit_margin) * 100

    @staticmethod
    def magic_number(arr_growth, sales_marketing_expense):
        """
        SaaS Magic Number
        = Net New ARR / Sales & Marketing Spend
        > 1.0: Very efficient
        0.75-1.0: Good
        < 0.75: Needs improvement
        """
        if sales_marketing_expense is None or sales_marketing_expense <= 0:
            return np.nan
        return arr_growth / sales_marketing_expense if arr_growth is not None else np.nan


class FinancialMetrics:
    """Financial sector specific metrics"""

    @staticmethod
    def net_interest_margin(net_interest_income, average_earning_assets):
        """NIM = Net Interest Income / Average Earning Assets"""
        if average_earning_assets is None or average_earning_assets <= 0:
            return np.nan
        return net_interest_income / average_earning_assets if net_interest_income is not None else np.nan

    @staticmethod
    def loan_to_deposit_ratio(total_loans, total_deposits):
        """Loan-to-Deposit Ratio"""
        if total_deposits is None or total_deposits <= 0:
            return np.nan
        return total_loans / total_deposits if total_loans is not None else np.nan

    @staticmethod
    def efficiency_ratio(non_interest_expense, revenue):
        """Efficiency Ratio = Non-Interest Expense / Revenue"""
        if revenue is None or revenue <= 0:
            return np.nan
        return non_interest_expense / revenue if non_interest_expense is not None else np.nan

    @staticmethod
    def tier1_capital_ratio(tier1_capital, risk_weighted_assets):
        """Tier 1 Capital Ratio"""
        if risk_weighted_assets is None or risk_weighted_assets <= 0:
            return np.nan
        return tier1_capital / risk_weighted_assets if tier1_capital is not None else np.nan


class EnergyMetrics:
    """Energy sector specific metrics"""

    @staticmethod
    def reserve_replacement_ratio(reserves_added, production):
        """Reserve Replacement Ratio = Reserves Added / Production"""
        if production is None or production <= 0:
            return np.nan
        return reserves_added / production if reserves_added is not None else np.nan

    @staticmethod
    def finding_cost(exploration_cost, reserves_found):
        """Finding Cost = Exploration Cost / Reserves Found"""
        if reserves_found is None or reserves_found <= 0:
            return np.nan
        return exploration_cost / reserves_found if exploration_cost is not None else np.nan

    @staticmethod
    def netback(revenue_per_boe, operating_cost_per_boe, royalties_per_boe):
        """Netback = Revenue - Operating Costs - Royalties (per BOE)"""
        if any(x is None for x in [revenue_per_boe, operating_cost_per_boe]):
            return np.nan
        return revenue_per_boe - operating_cost_per_boe - (royalties_per_boe or 0)


# =============================================================================
# COMPREHENSIVE CALCULATOR
# =============================================================================

def calculate_all_metrics(stock_data, price_history=None, benchmark_data=None, sector_data=None):
    """
    Calculate all available metrics for a stock

    Args:
        stock_data: Dictionary with fundamental data
        price_history: DataFrame with OHLCV data
        benchmark_data: DataFrame with benchmark prices (e.g., SPY)
        sector_data: DataFrame with sector peer data

    Returns:
        Dictionary with all calculated metrics
    """
    metrics = {}

    # -------------------------------------------------------------------------
    # Performance Metrics (if price history available)
    # -------------------------------------------------------------------------
    if price_history is not None and len(price_history) > 20:
        prices = price_history['Close']
        returns = prices.pct_change().dropna()

        # Absolute Performance
        metrics['cumulative_return'] = PerformanceMetrics.cumulative_return(prices)
        metrics['annualized_return'] = PerformanceMetrics.annualized_return(prices)

        max_dd, peak, trough, recovery = PerformanceMetrics.max_drawdown(prices)
        metrics['max_drawdown'] = max_dd
        metrics['recovery_time_days'] = recovery

        metrics['volatility'] = PerformanceMetrics.volatility(returns)
        metrics['downside_volatility'] = PerformanceMetrics.downside_volatility(returns)
        metrics['sharpe_ratio'] = PerformanceMetrics.sharpe_ratio(returns)
        metrics['sortino_ratio'] = PerformanceMetrics.sortino_ratio(returns)
        metrics['calmar_ratio'] = PerformanceMetrics.calmar_ratio(prices, returns)
        metrics['omega_ratio'] = PerformanceMetrics.omega_ratio(returns)
        metrics['var_95'] = PerformanceMetrics.calculate_var(returns, 0.95)
        metrics['cvar_95'] = PerformanceMetrics.calculate_cvar(returns, 0.95)

        # Relative Performance (if benchmark available)
        if benchmark_data is not None and len(benchmark_data) > 20:
            bench_prices = benchmark_data['Close']
            bench_returns = bench_prices.pct_change().dropna()

            alpha, beta = RelativePerformanceMetrics.alpha_beta(returns, bench_returns)
            metrics['alpha'] = alpha
            metrics['beta'] = beta
            metrics['tracking_error'] = RelativePerformanceMetrics.tracking_error(returns, bench_returns)
            metrics['information_ratio'] = RelativePerformanceMetrics.information_ratio(returns, bench_returns)
            metrics['r_squared'] = RelativePerformanceMetrics.r_squared(returns, bench_returns)

            up_cap, down_cap = RelativePerformanceMetrics.up_down_capture(returns, bench_returns)
            metrics['up_capture'] = up_cap
            metrics['down_capture'] = down_cap

    # -------------------------------------------------------------------------
    # Fundamental Metrics
    # -------------------------------------------------------------------------

    # Profitability
    metrics['gross_margin'] = stock_data.get('gross_margin')
    metrics['operating_margin'] = stock_data.get('operating_margin')
    metrics['profit_margin'] = stock_data.get('profit_margin')
    metrics['ebitda_margin'] = stock_data.get('ebitda_margin')
    metrics['roe'] = stock_data.get('roe')
    metrics['roa'] = stock_data.get('roa')

    # Calculate ROIC if components available
    if all(k in stock_data for k in ['net_income', 'total_debt', 'total_equity', 'total_cash']):
        metrics['roic'] = ProfitabilityMetrics.calculate_roic_from_data(
            stock_data.get('net_income'),
            stock_data.get('total_debt'),
            stock_data.get('total_equity'),
            stock_data.get('total_cash')
        )

    # Valuation
    metrics['forward_pe'] = stock_data.get('forward_pe')
    metrics['trailing_pe'] = stock_data.get('trailing_pe')
    metrics['peg_ratio'] = stock_data.get('peg_ratio')
    metrics['price_to_book'] = stock_data.get('price_to_book')
    metrics['price_to_sales'] = stock_data.get('price_to_sales')
    metrics['ev_to_ebitda'] = stock_data.get('ev_to_ebitda')
    metrics['ev_to_revenue'] = stock_data.get('ev_to_revenue')
    metrics['dividend_yield'] = stock_data.get('dividend_yield')

    # FCF Yield
    if stock_data.get('free_cashflow') and stock_data.get('market_cap'):
        metrics['fcf_yield'] = ValuationMetrics.fcf_yield(
            stock_data['free_cashflow'],
            stock_data['market_cap']
        )

    # Growth
    metrics['revenue_growth'] = stock_data.get('revenue_growth')
    metrics['earnings_growth'] = stock_data.get('earnings_growth')

    # Financial Stability
    metrics['current_ratio'] = stock_data.get('current_ratio')
    metrics['quick_ratio'] = stock_data.get('quick_ratio')
    metrics['debt_to_equity'] = stock_data.get('debt_to_equity')

    # Net Debt to EBITDA
    if all(k in stock_data for k in ['total_debt', 'total_cash', 'ebitda']):
        metrics['net_debt_to_ebitda'] = FinancialStabilityMetrics.net_debt_to_ebitda(
            stock_data.get('total_debt'),
            stock_data.get('total_cash'),
            stock_data.get('ebitda')
        )

    # Interest Coverage
    if all(k in stock_data for k in ['ebit', 'interest_expense']):
        metrics['interest_coverage'] = FinancialStabilityMetrics.interest_coverage(
            stock_data.get('ebit'),
            stock_data.get('interest_expense')
        )

    # -------------------------------------------------------------------------
    # Composite Scores
    # -------------------------------------------------------------------------

    # Altman Z-Score
    if all(k in stock_data for k in ['working_capital', 'total_assets', 'retained_earnings',
                                      'ebit', 'market_cap', 'total_liabilities', 'total_revenue']):
        metrics['altman_z_score'] = CompositeScores.altman_z_score(
            stock_data.get('working_capital'),
            stock_data.get('total_assets'),
            stock_data.get('retained_earnings'),
            stock_data.get('ebit'),
            stock_data.get('market_cap'),
            stock_data.get('total_liabilities'),
            stock_data.get('total_revenue')
        )
        metrics['z_score_interpretation'] = CompositeScores.interpret_z_score(metrics['altman_z_score'])

    # Piotroski F-Score
    metrics['piotroski_f_score'] = CompositeScores.piotroski_f_score(stock_data)
    metrics['f_score_interpretation'] = CompositeScores.interpret_f_score(metrics['piotroski_f_score'])

    # Quality Score
    metrics['quality_score'] = CompositeScores.quality_score(stock_data)

    # -------------------------------------------------------------------------
    # Industry-Specific (if applicable)
    # -------------------------------------------------------------------------
    sector = stock_data.get('sector', '')

    if 'Technology' in str(sector) or 'Information Technology' in str(sector):
        if stock_data.get('rd_expense') and stock_data.get('total_revenue'):
            metrics['rd_to_sales'] = TechMetrics.rd_to_sales(
                stock_data['rd_expense'],
                stock_data['total_revenue']
            )
        if stock_data.get('revenue_growth') and stock_data.get('profit_margin'):
            metrics['rule_of_40'] = TechMetrics.rule_of_40(
                stock_data['revenue_growth'],
                stock_data['profit_margin']
            )

    return metrics


# =============================================================================
# SECTOR RELATIVE CALCULATIONS
# =============================================================================

def calculate_sector_percentiles(df, metrics_columns):
    """Calculate percentile ranks within sector for specified metrics"""
    result = df.copy()

    for metric in metrics_columns:
        if metric in df.columns:
            col_name = f'{metric}_sector_percentile'
            result[col_name] = df.groupby('sector')[metric].transform(
                lambda x: x.rank(pct=True) * 100
            )

    return result


def calculate_sector_relative(df, metrics_columns):
    """Calculate metrics relative to sector median"""
    result = df.copy()

    for metric in metrics_columns:
        if metric in df.columns:
            col_name = f'{metric}_vs_sector'
            sector_medians = df.groupby('sector')[metric].transform('median')
            result[col_name] = df[metric] / sector_medians

    return result
