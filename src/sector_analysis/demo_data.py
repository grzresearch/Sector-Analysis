"""
Demo Data Generator
Creates realistic simulated stock data for demonstration purposes
when internet access is restricted
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Sector characteristics (for realistic data generation)
SECTOR_PROFILES = {
    'Technology': {
        'pe_range': (15, 45),
        'pb_range': (3, 15),
        'de_range': (0, 100),
        'roe_range': (0.10, 0.35),
        'margin_range': (0.15, 0.35),
        'growth_range': (0.05, 0.25),
        'return_range': (-0.10, 0.40),
        'volatility_range': (0.25, 0.45),
        'beta_range': (1.0, 1.5),
    },
    'Health Care': {
        'pe_range': (12, 35),
        'pb_range': (2, 10),
        'de_range': (20, 150),
        'roe_range': (0.08, 0.25),
        'margin_range': (0.10, 0.25),
        'growth_range': (0.02, 0.15),
        'return_range': (-0.05, 0.25),
        'volatility_range': (0.20, 0.35),
        'beta_range': (0.7, 1.2),
    },
    'Financials': {
        'pe_range': (8, 20),
        'pb_range': (0.8, 2.5),
        'de_range': (100, 500),
        'roe_range': (0.08, 0.18),
        'margin_range': (0.15, 0.30),
        'growth_range': (0.00, 0.10),
        'return_range': (-0.15, 0.20),
        'volatility_range': (0.20, 0.35),
        'beta_range': (1.0, 1.4),
    },
    'Consumer Discretionary': {
        'pe_range': (12, 35),
        'pb_range': (2, 12),
        'de_range': (30, 200),
        'roe_range': (0.10, 0.30),
        'margin_range': (0.05, 0.20),
        'growth_range': (0.00, 0.15),
        'return_range': (-0.10, 0.30),
        'volatility_range': (0.25, 0.40),
        'beta_range': (1.0, 1.5),
    },
    'Consumer Staples': {
        'pe_range': (15, 28),
        'pb_range': (3, 10),
        'de_range': (50, 150),
        'roe_range': (0.15, 0.35),
        'margin_range': (0.08, 0.18),
        'growth_range': (0.01, 0.08),
        'return_range': (-0.05, 0.15),
        'volatility_range': (0.12, 0.22),
        'beta_range': (0.5, 0.9),
    },
    'Industrials': {
        'pe_range': (12, 28),
        'pb_range': (2, 8),
        'de_range': (40, 180),
        'roe_range': (0.10, 0.25),
        'margin_range': (0.06, 0.15),
        'growth_range': (0.00, 0.12),
        'return_range': (-0.08, 0.22),
        'volatility_range': (0.20, 0.32),
        'beta_range': (0.9, 1.3),
    },
    'Energy': {
        'pe_range': (8, 18),
        'pb_range': (1, 3),
        'de_range': (30, 120),
        'roe_range': (0.05, 0.20),
        'margin_range': (0.05, 0.15),
        'growth_range': (-0.10, 0.20),
        'return_range': (-0.25, 0.35),
        'volatility_range': (0.30, 0.50),
        'beta_range': (1.0, 1.6),
    },
    'Communication Services': {
        'pe_range': (12, 30),
        'pb_range': (1.5, 8),
        'de_range': (50, 200),
        'roe_range': (0.08, 0.22),
        'margin_range': (0.10, 0.25),
        'growth_range': (0.00, 0.12),
        'return_range': (-0.15, 0.25),
        'volatility_range': (0.22, 0.38),
        'beta_range': (0.9, 1.3),
    },
    'Materials': {
        'pe_range': (10, 22),
        'pb_range': (1.5, 5),
        'de_range': (30, 120),
        'roe_range': (0.08, 0.20),
        'margin_range': (0.08, 0.18),
        'growth_range': (-0.05, 0.12),
        'return_range': (-0.12, 0.22),
        'volatility_range': (0.22, 0.38),
        'beta_range': (1.0, 1.4),
    },
    'Real Estate': {
        'pe_range': (20, 50),
        'pb_range': (1.2, 4),
        'de_range': (80, 250),
        'roe_range': (0.04, 0.12),
        'margin_range': (0.25, 0.50),
        'growth_range': (0.02, 0.10),
        'return_range': (-0.10, 0.18),
        'volatility_range': (0.18, 0.30),
        'beta_range': (0.7, 1.1),
    },
    'Utilities': {
        'pe_range': (14, 25),
        'pb_range': (1.2, 3),
        'de_range': (80, 180),
        'roe_range': (0.06, 0.12),
        'margin_range': (0.10, 0.20),
        'growth_range': (0.01, 0.06),
        'return_range': (-0.05, 0.12),
        'volatility_range': (0.12, 0.22),
        'beta_range': (0.3, 0.7),
    },
}


# Sample stock data
DEMO_STOCKS = {
    'Technology': [
        ('AAPL', 'Apple Inc.', 3000),
        ('MSFT', 'Microsoft Corp.', 2800),
        ('GOOGL', 'Alphabet Inc.', 1800),
        ('AMZN', 'Amazon.com Inc.', 1500),
        ('NVDA', 'NVIDIA Corp.', 1200),
        ('META', 'Meta Platforms Inc.', 900),
        ('TSLA', 'Tesla Inc.', 800),
        ('AMD', 'Advanced Micro Devices', 250),
        ('INTC', 'Intel Corp.', 150),
        ('CRM', 'Salesforce Inc.', 280),
        ('ORCL', 'Oracle Corp.', 350),
        ('CSCO', 'Cisco Systems', 220),
        ('ADBE', 'Adobe Inc.', 240),
        ('AVGO', 'Broadcom Inc.', 600),
        ('TXN', 'Texas Instruments', 180),
    ],
    'Health Care': [
        ('JNJ', 'Johnson & Johnson', 380),
        ('UNH', 'UnitedHealth Group', 480),
        ('PFE', 'Pfizer Inc.', 160),
        ('ABBV', 'AbbVie Inc.', 280),
        ('MRK', 'Merck & Co.', 260),
        ('LLY', 'Eli Lilly', 750),
        ('TMO', 'Thermo Fisher', 200),
        ('ABT', 'Abbott Labs', 190),
        ('DHR', 'Danaher Corp.', 170),
        ('BMY', 'Bristol-Myers Squibb', 110),
        ('AMGN', 'Amgen Inc.', 140),
        ('GILD', 'Gilead Sciences', 100),
    ],
    'Financials': [
        ('JPM', 'JPMorgan Chase', 550),
        ('BAC', 'Bank of America', 280),
        ('WFC', 'Wells Fargo', 180),
        ('GS', 'Goldman Sachs', 150),
        ('MS', 'Morgan Stanley', 140),
        ('BLK', 'BlackRock Inc.', 120),
        ('C', 'Citigroup Inc.', 100),
        ('AXP', 'American Express', 160),
        ('SCHW', 'Charles Schwab', 110),
        ('USB', 'US Bancorp', 60),
        ('PNC', 'PNC Financial', 70),
        ('COF', 'Capital One', 50),
    ],
    'Consumer Discretionary': [
        ('HD', 'Home Depot', 380),
        ('NKE', 'Nike Inc.', 140),
        ('MCD', 'McDonalds Corp.', 200),
        ('SBUX', 'Starbucks Corp.', 100),
        ('LOW', 'Lowes Companies', 140),
        ('TGT', 'Target Corp.', 65),
        ('TJX', 'TJX Companies', 110),
        ('BKNG', 'Booking Holdings', 130),
        ('F', 'Ford Motor', 45),
        ('GM', 'General Motors', 55),
        ('ROST', 'Ross Stores', 45),
        ('MAR', 'Marriott Intl', 70),
    ],
    'Consumer Staples': [
        ('PG', 'Procter & Gamble', 380),
        ('KO', 'Coca-Cola Co.', 260),
        ('PEP', 'PepsiCo Inc.', 230),
        ('COST', 'Costco Wholesale', 350),
        ('WMT', 'Walmart Inc.', 480),
        ('PM', 'Philip Morris', 150),
        ('MO', 'Altria Group', 80),
        ('MDLZ', 'Mondelez Intl', 90),
        ('CL', 'Colgate-Palmolive', 75),
        ('KMB', 'Kimberly-Clark', 45),
    ],
    'Industrials': [
        ('CAT', 'Caterpillar Inc.', 180),
        ('BA', 'Boeing Co.', 120),
        ('HON', 'Honeywell Intl', 140),
        ('UPS', 'United Parcel Service', 100),
        ('RTX', 'RTX Corp.', 140),
        ('GE', 'GE Aerospace', 180),
        ('DE', 'Deere & Co.', 110),
        ('LMT', 'Lockheed Martin', 120),
        ('UNP', 'Union Pacific', 150),
        ('MMM', '3M Company', 60),
        ('FDX', 'FedEx Corp.', 65),
        ('NOC', 'Northrop Grumman', 75),
    ],
    'Energy': [
        ('XOM', 'Exxon Mobil', 460),
        ('CVX', 'Chevron Corp.', 280),
        ('COP', 'ConocoPhillips', 130),
        ('SLB', 'Schlumberger', 65),
        ('EOG', 'EOG Resources', 70),
        ('MPC', 'Marathon Petroleum', 55),
        ('PSX', 'Phillips 66', 50),
        ('VLO', 'Valero Energy', 40),
        ('OXY', 'Occidental Petroleum', 45),
        ('HAL', 'Halliburton', 30),
    ],
    'Communication Services': [
        ('DIS', 'Walt Disney', 180),
        ('NFLX', 'Netflix Inc.', 300),
        ('CMCSA', 'Comcast Corp.', 150),
        ('VZ', 'Verizon Comm.', 160),
        ('T', 'AT&T Inc.', 140),
        ('TMUS', 'T-Mobile US', 200),
        ('EA', 'Electronic Arts', 35),
        ('TTWO', 'Take-Two Interactive', 25),
    ],
    'Materials': [
        ('LIN', 'Linde PLC', 200),
        ('APD', 'Air Products', 65),
        ('SHW', 'Sherwin-Williams', 85),
        ('ECL', 'Ecolab Inc.', 60),
        ('FCX', 'Freeport-McMoRan', 60),
        ('NEM', 'Newmont Corp.', 45),
        ('NUE', 'Nucor Corp.', 40),
        ('DOW', 'Dow Inc.', 35),
    ],
    'Real Estate': [
        ('AMT', 'American Tower', 100),
        ('PLD', 'Prologis Inc.', 110),
        ('CCI', 'Crown Castle', 45),
        ('EQIX', 'Equinix Inc.', 80),
        ('PSA', 'Public Storage', 55),
        ('WELL', 'Welltower Inc.', 50),
        ('SPG', 'Simon Property', 50),
        ('O', 'Realty Income', 45),
    ],
    'Utilities': [
        ('NEE', 'NextEra Energy', 150),
        ('DUK', 'Duke Energy', 80),
        ('SO', 'Southern Company', 85),
        ('D', 'Dominion Energy', 45),
        ('AEP', 'American Electric', 50),
        ('SRE', 'Sempra Energy', 50),
        ('EXC', 'Exelon Corp.', 40),
        ('XEL', 'Xcel Energy', 35),
    ],
}


def random_in_range(range_tuple):
    """Generate random value in range"""
    return np.random.uniform(range_tuple[0], range_tuple[1])


def generate_demo_stock(ticker, name, sector, market_cap_b):
    """Generate demo data for a single stock"""
    profile = SECTOR_PROFILES[sector]

    # Add some randomness to market cap
    market_cap = market_cap_b * 1e9 * np.random.uniform(0.9, 1.1)

    # Generate price (assume some EPS and PE relationship)
    forward_pe = random_in_range(profile['pe_range'])
    eps = np.random.uniform(2, 15)
    price = eps * forward_pe * np.random.uniform(0.8, 1.2)

    # Profitability
    roe = random_in_range(profile['roe_range'])
    profit_margin = random_in_range(profile['margin_range'])
    gross_margin = profit_margin + np.random.uniform(0.15, 0.35)
    operating_margin = profit_margin + np.random.uniform(0.05, 0.15)
    roa = roe * np.random.uniform(0.3, 0.6)

    # Financial health
    debt_to_equity = random_in_range(profile['de_range'])
    current_ratio = np.random.uniform(0.8, 2.5)
    quick_ratio = current_ratio * np.random.uniform(0.6, 0.9)

    # Growth
    revenue_growth = random_in_range(profile['growth_range'])
    earnings_growth = revenue_growth + np.random.uniform(-0.05, 0.10)

    # Performance
    one_year_return = random_in_range(profile['return_range'])
    volatility = random_in_range(profile['volatility_range'])
    beta = random_in_range(profile['beta_range'])

    # Calculate derived metrics
    total_revenue = market_cap / forward_pe * np.random.uniform(0.5, 2)
    ebitda = total_revenue * operating_margin * np.random.uniform(1.0, 1.3)
    free_cashflow = ebitda * np.random.uniform(0.3, 0.7)
    operating_cashflow = ebitda * np.random.uniform(0.7, 1.0)
    total_debt = market_cap * debt_to_equity / 100
    total_cash = total_debt * np.random.uniform(0.1, 0.5)
    net_income = total_revenue * profit_margin

    return {
        'ticker': ticker,
        'name': name,
        'sector': sector,
        'industry': f'{sector} Industry',
        'index': 'S&P500',
        'market_cap': market_cap,
        'current_price': price,

        # Valuation
        'forward_pe': forward_pe,
        'trailing_pe': forward_pe * np.random.uniform(0.9, 1.2),
        'peg_ratio': forward_pe / (revenue_growth * 100 + 1) if revenue_growth > 0 else np.nan,
        'price_to_book': random_in_range(profile['pb_range']),
        'price_to_sales': market_cap / total_revenue if total_revenue > 0 else np.nan,
        'ev_to_ebitda': (market_cap + total_debt - total_cash) / ebitda if ebitda > 0 else np.nan,
        'ev_to_revenue': (market_cap + total_debt - total_cash) / total_revenue if total_revenue > 0 else np.nan,

        # Profitability
        'profit_margin': profit_margin,
        'operating_margin': operating_margin,
        'gross_margin': gross_margin,
        'roe': roe,
        'roa': roa,

        # Financial health
        'debt_to_equity': debt_to_equity,
        'current_ratio': current_ratio,
        'quick_ratio': quick_ratio,
        'total_debt': total_debt,
        'total_cash': total_cash,

        # Growth
        'revenue_growth': revenue_growth,
        'earnings_growth': earnings_growth,
        'earnings_quarterly_growth': earnings_growth * np.random.uniform(0.8, 1.2),

        # Cash flow
        'free_cashflow': free_cashflow,
        'operating_cashflow': operating_cashflow,

        # Dividend
        'dividend_yield': np.random.uniform(0, 0.04) if sector in ['Utilities', 'Consumer Staples', 'Real Estate'] else np.random.uniform(0, 0.02),
        'payout_ratio': np.random.uniform(0.2, 0.6),

        # Price metrics
        'beta': beta,
        'fifty_two_week_high': price * np.random.uniform(1.05, 1.30),
        'fifty_two_week_low': price * np.random.uniform(0.70, 0.95),
        'fifty_day_average': price * np.random.uniform(0.95, 1.05),
        'two_hundred_day_average': price * np.random.uniform(0.90, 1.10),

        # EPS
        'trailing_eps': eps,
        'forward_eps': eps * (1 + earnings_growth),

        # Revenue/Earnings
        'total_revenue': total_revenue,
        'ebitda': ebitda,
        'net_income': net_income,

        # Analyst targets
        'target_high_price': price * np.random.uniform(1.15, 1.50),
        'target_low_price': price * np.random.uniform(0.70, 0.95),
        'target_mean_price': price * np.random.uniform(1.00, 1.20),
        'recommendation_mean': np.random.uniform(1.5, 3.5),

        # Returns
        '1y_return': one_year_return,
        '6m_return': one_year_return * np.random.uniform(0.3, 0.7),
        '3m_return': one_year_return * np.random.uniform(0.1, 0.4),
        '1m_return': one_year_return * np.random.uniform(0.02, 0.15),
        'volatility': volatility,
        'sharpe_approx': (one_year_return - 0.04) / volatility if volatility > 0 else np.nan,
    }


def generate_demo_dataset():
    """Generate complete demo dataset"""
    data = []

    for sector, stocks in DEMO_STOCKS.items():
        for ticker, name, market_cap_b in stocks:
            stock_data = generate_demo_stock(ticker, name, sector, market_cap_b)
            data.append(stock_data)

    df = pd.DataFrame(data)

    print(f"Generated demo dataset with {len(df)} stocks across {df['sector'].nunique()} sectors")

    return df


def generate_demo_price_history(days=252):
    """Generate demo price history for technical analysis"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')

    # Generate random walk price series
    returns = np.random.normal(0.0004, 0.015, days)
    prices = 100 * np.exp(np.cumsum(returns))

    # Generate volume
    base_volume = 1000000
    volume = base_volume * np.random.lognormal(0, 0.5, days)

    # Create OHLCV data
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * np.random.uniform(0.99, 1.01, days),
        'High': prices * np.random.uniform(1.00, 1.02, days),
        'Low': prices * np.random.uniform(0.98, 1.00, days),
        'Close': prices,
        'Volume': volume.astype(int)
    })
    df.set_index('Date', inplace=True)

    return df


if __name__ == "__main__":
    # Test demo data generation
    df = generate_demo_dataset()
    print(df.head())
    print("\nSector distribution:")
    print(df['sector'].value_counts())
