"""
Data Fetcher Module
Fetches S&P 500 and Nasdaq stock data using Yahoo Finance API
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import warnings
warnings.filterwarnings('ignore')


# Fallback ticker list with sectors (subset of S&P 500 and Nasdaq)
FALLBACK_TICKERS = {
    # Technology
    'AAPL': ('Apple Inc.', 'Technology'),
    'MSFT': ('Microsoft Corp.', 'Technology'),
    'GOOGL': ('Alphabet Inc.', 'Technology'),
    'AMZN': ('Amazon.com Inc.', 'Technology'),
    'NVDA': ('NVIDIA Corp.', 'Technology'),
    'META': ('Meta Platforms Inc.', 'Technology'),
    'TSLA': ('Tesla Inc.', 'Technology'),
    'AMD': ('Advanced Micro Devices', 'Technology'),
    'INTC': ('Intel Corp.', 'Technology'),
    'CRM': ('Salesforce Inc.', 'Technology'),
    'ORCL': ('Oracle Corp.', 'Technology'),
    'CSCO': ('Cisco Systems', 'Technology'),
    'ADBE': ('Adobe Inc.', 'Technology'),
    'AVGO': ('Broadcom Inc.', 'Technology'),
    'TXN': ('Texas Instruments', 'Technology'),
    'QCOM': ('Qualcomm Inc.', 'Technology'),
    'IBM': ('IBM Corp.', 'Technology'),
    'NOW': ('ServiceNow Inc.', 'Technology'),
    'INTU': ('Intuit Inc.', 'Technology'),
    'AMAT': ('Applied Materials', 'Technology'),

    # Health Care
    'JNJ': ('Johnson & Johnson', 'Health Care'),
    'UNH': ('UnitedHealth Group', 'Health Care'),
    'PFE': ('Pfizer Inc.', 'Health Care'),
    'ABBV': ('AbbVie Inc.', 'Health Care'),
    'MRK': ('Merck & Co.', 'Health Care'),
    'LLY': ('Eli Lilly', 'Health Care'),
    'TMO': ('Thermo Fisher', 'Health Care'),
    'ABT': ('Abbott Labs', 'Health Care'),
    'DHR': ('Danaher Corp.', 'Health Care'),
    'BMY': ('Bristol-Myers Squibb', 'Health Care'),
    'AMGN': ('Amgen Inc.', 'Health Care'),
    'GILD': ('Gilead Sciences', 'Health Care'),
    'CVS': ('CVS Health', 'Health Care'),
    'ISRG': ('Intuitive Surgical', 'Health Care'),
    'VRTX': ('Vertex Pharma', 'Health Care'),

    # Financials
    'JPM': ('JPMorgan Chase', 'Financials'),
    'BAC': ('Bank of America', 'Financials'),
    'WFC': ('Wells Fargo', 'Financials'),
    'GS': ('Goldman Sachs', 'Financials'),
    'MS': ('Morgan Stanley', 'Financials'),
    'BLK': ('BlackRock Inc.', 'Financials'),
    'C': ('Citigroup Inc.', 'Financials'),
    'AXP': ('American Express', 'Financials'),
    'SCHW': ('Charles Schwab', 'Financials'),
    'USB': ('US Bancorp', 'Financials'),
    'PNC': ('PNC Financial', 'Financials'),
    'TFC': ('Truist Financial', 'Financials'),
    'COF': ('Capital One', 'Financials'),
    'BK': ('Bank of NY Mellon', 'Financials'),
    'CME': ('CME Group', 'Financials'),

    # Consumer Discretionary
    'HD': ('Home Depot', 'Consumer Discretionary'),
    'NKE': ('Nike Inc.', 'Consumer Discretionary'),
    'MCD': ('McDonalds Corp.', 'Consumer Discretionary'),
    'SBUX': ('Starbucks Corp.', 'Consumer Discretionary'),
    'LOW': ('Lowes Companies', 'Consumer Discretionary'),
    'TGT': ('Target Corp.', 'Consumer Discretionary'),
    'TJX': ('TJX Companies', 'Consumer Discretionary'),
    'BKNG': ('Booking Holdings', 'Consumer Discretionary'),
    'F': ('Ford Motor', 'Consumer Discretionary'),
    'GM': ('General Motors', 'Consumer Discretionary'),
    'ROST': ('Ross Stores', 'Consumer Discretionary'),
    'MAR': ('Marriott Intl', 'Consumer Discretionary'),
    'YUM': ('Yum Brands', 'Consumer Discretionary'),
    'DHI': ('D.R. Horton', 'Consumer Discretionary'),
    'ORLY': ('OReilly Auto', 'Consumer Discretionary'),

    # Consumer Staples
    'PG': ('Procter & Gamble', 'Consumer Staples'),
    'KO': ('Coca-Cola Co.', 'Consumer Staples'),
    'PEP': ('PepsiCo Inc.', 'Consumer Staples'),
    'COST': ('Costco Wholesale', 'Consumer Staples'),
    'WMT': ('Walmart Inc.', 'Consumer Staples'),
    'PM': ('Philip Morris', 'Consumer Staples'),
    'MO': ('Altria Group', 'Consumer Staples'),
    'MDLZ': ('Mondelez Intl', 'Consumer Staples'),
    'CL': ('Colgate-Palmolive', 'Consumer Staples'),
    'KMB': ('Kimberly-Clark', 'Consumer Staples'),
    'GIS': ('General Mills', 'Consumer Staples'),
    'KHC': ('Kraft Heinz', 'Consumer Staples'),
    'SYY': ('Sysco Corp.', 'Consumer Staples'),
    'STZ': ('Constellation Brands', 'Consumer Staples'),
    'K': ('Kellanova', 'Consumer Staples'),

    # Industrials
    'CAT': ('Caterpillar Inc.', 'Industrials'),
    'BA': ('Boeing Co.', 'Industrials'),
    'HON': ('Honeywell Intl', 'Industrials'),
    'UPS': ('United Parcel Service', 'Industrials'),
    'RTX': ('RTX Corp.', 'Industrials'),
    'GE': ('GE Aerospace', 'Industrials'),
    'DE': ('Deere & Co.', 'Industrials'),
    'LMT': ('Lockheed Martin', 'Industrials'),
    'UNP': ('Union Pacific', 'Industrials'),
    'MMM': ('3M Company', 'Industrials'),
    'FDX': ('FedEx Corp.', 'Industrials'),
    'NOC': ('Northrop Grumman', 'Industrials'),
    'GD': ('General Dynamics', 'Industrials'),
    'CSX': ('CSX Corp.', 'Industrials'),
    'EMR': ('Emerson Electric', 'Industrials'),

    # Energy
    'XOM': ('Exxon Mobil', 'Energy'),
    'CVX': ('Chevron Corp.', 'Energy'),
    'COP': ('ConocoPhillips', 'Energy'),
    'SLB': ('Schlumberger', 'Energy'),
    'EOG': ('EOG Resources', 'Energy'),
    'MPC': ('Marathon Petroleum', 'Energy'),
    'PSX': ('Phillips 66', 'Energy'),
    'VLO': ('Valero Energy', 'Energy'),
    'OXY': ('Occidental Petroleum', 'Energy'),
    'WMB': ('Williams Companies', 'Energy'),
    'KMI': ('Kinder Morgan', 'Energy'),
    'HAL': ('Halliburton', 'Energy'),
    'DVN': ('Devon Energy', 'Energy'),
    'BKR': ('Baker Hughes', 'Energy'),
    'FANG': ('Diamondback Energy', 'Energy'),

    # Communication Services
    'DIS': ('Walt Disney', 'Communication Services'),
    'NFLX': ('Netflix Inc.', 'Communication Services'),
    'CMCSA': ('Comcast Corp.', 'Communication Services'),
    'VZ': ('Verizon Comm.', 'Communication Services'),
    'T': ('AT&T Inc.', 'Communication Services'),
    'TMUS': ('T-Mobile US', 'Communication Services'),
    'CHTR': ('Charter Comm.', 'Communication Services'),
    'EA': ('Electronic Arts', 'Communication Services'),
    'WBD': ('Warner Bros Discovery', 'Communication Services'),
    'TTWO': ('Take-Two Interactive', 'Communication Services'),
    'OMC': ('Omnicom Group', 'Communication Services'),
    'IPG': ('Interpublic Group', 'Communication Services'),
    'PARA': ('Paramount Global', 'Communication Services'),
    'FOX': ('Fox Corp.', 'Communication Services'),
    'MTCH': ('Match Group', 'Communication Services'),

    # Materials
    'LIN': ('Linde PLC', 'Materials'),
    'APD': ('Air Products', 'Materials'),
    'SHW': ('Sherwin-Williams', 'Materials'),
    'ECL': ('Ecolab Inc.', 'Materials'),
    'FCX': ('Freeport-McMoRan', 'Materials'),
    'NEM': ('Newmont Corp.', 'Materials'),
    'NUE': ('Nucor Corp.', 'Materials'),
    'DOW': ('Dow Inc.', 'Materials'),
    'DD': ('DuPont', 'Materials'),
    'PPG': ('PPG Industries', 'Materials'),
    'VMC': ('Vulcan Materials', 'Materials'),
    'MLM': ('Martin Marietta', 'Materials'),
    'ALB': ('Albemarle Corp.', 'Materials'),
    'CTVA': ('Corteva Inc.', 'Materials'),
    'IFF': ('Intl Flavors', 'Materials'),

    # Real Estate
    'AMT': ('American Tower', 'Real Estate'),
    'PLD': ('Prologis Inc.', 'Real Estate'),
    'CCI': ('Crown Castle', 'Real Estate'),
    'EQIX': ('Equinix Inc.', 'Real Estate'),
    'PSA': ('Public Storage', 'Real Estate'),
    'WELL': ('Welltower Inc.', 'Real Estate'),
    'SPG': ('Simon Property', 'Real Estate'),
    'DLR': ('Digital Realty', 'Real Estate'),
    'O': ('Realty Income', 'Real Estate'),
    'VICI': ('VICI Properties', 'Real Estate'),
    'AVB': ('AvalonBay Comm.', 'Real Estate'),
    'EQR': ('Equity Residential', 'Real Estate'),
    'WY': ('Weyerhaeuser', 'Real Estate'),
    'ARE': ('Alexandria RE', 'Real Estate'),
    'MAA': ('Mid-America Apt', 'Real Estate'),

    # Utilities
    'NEE': ('NextEra Energy', 'Utilities'),
    'DUK': ('Duke Energy', 'Utilities'),
    'SO': ('Southern Company', 'Utilities'),
    'D': ('Dominion Energy', 'Utilities'),
    'AEP': ('American Electric', 'Utilities'),
    'SRE': ('Sempra Energy', 'Utilities'),
    'EXC': ('Exelon Corp.', 'Utilities'),
    'XEL': ('Xcel Energy', 'Utilities'),
    'PCG': ('PG&E Corp.', 'Utilities'),
    'WEC': ('WEC Energy', 'Utilities'),
    'ED': ('Consolidated Edison', 'Utilities'),
    'EIX': ('Edison Intl', 'Utilities'),
    'AWK': ('American Water', 'Utilities'),
    'DTE': ('DTE Energy', 'Utilities'),
    'AEE': ('Ameren Corp.', 'Utilities'),
}


def get_fallback_tickers():
    """Get fallback ticker list when web scraping fails"""
    data = []
    for ticker, (name, sector) in FALLBACK_TICKERS.items():
        data.append({
            'ticker': ticker,
            'name': name,
            'sector': sector,
            'sub_industry': '',
            'index': 'S&P500'
        })
    return pd.DataFrame(data)


def get_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        return df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']].rename(
            columns={'Symbol': 'ticker', 'Security': 'name',
                     'GICS Sector': 'sector', 'GICS Sub-Industry': 'sub_industry'}
        )
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return pd.DataFrame()


def get_nasdaq100_tickers():
    """Fetch Nasdaq 100 tickers from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    try:
        tables = pd.read_html(url)
        # Find the table with tickers
        for table in tables:
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                ticker_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                company_col = 'Company' if 'Company' in table.columns else table.columns[0]
                sector_col = 'GICS Sector' if 'GICS Sector' in table.columns else None

                df = table[[ticker_col, company_col]].copy()
                df.columns = ['ticker', 'name']
                df['ticker'] = df['ticker'].str.replace('.', '-', regex=False)
                if sector_col:
                    df['sector'] = table[sector_col]
                return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching Nasdaq 100 tickers: {e}")
        return pd.DataFrame()


def get_combined_tickers():
    """Get combined unique tickers from S&P 500 and Nasdaq 100"""
    print("Fetching S&P 500 tickers...")
    sp500 = get_sp500_tickers()

    print("Fetching Nasdaq 100 tickers...")
    nasdaq = get_nasdaq100_tickers()

    # Check if web scraping succeeded
    if len(sp500) == 0 and len(nasdaq) == 0:
        print("Web scraping failed. Using fallback ticker list...")
        combined = get_fallback_tickers()
        print(f"Loaded {len(combined)} tickers from fallback list")
        return combined

    sp500['index'] = 'S&P500'
    nasdaq['index'] = 'NASDAQ100'

    # Combine and remove duplicates, keeping S&P 500 info as priority
    combined = pd.concat([sp500, nasdaq], ignore_index=True)
    combined = combined.drop_duplicates(subset='ticker', keep='first')

    print(f"Total unique tickers: {len(combined)}")
    return combined


def fetch_fundamental_data(ticker, max_retries=3):
    """Fetch fundamental data for a single ticker"""
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get balance sheet data
            try:
                balance_sheet = stock.balance_sheet
                quarterly_balance = stock.quarterly_balance_sheet
            except:
                balance_sheet = pd.DataFrame()
                quarterly_balance = pd.DataFrame()

            # Get income statement
            try:
                income_stmt = stock.income_stmt
                quarterly_income = stock.quarterly_income_stmt
            except:
                income_stmt = pd.DataFrame()
                quarterly_income = pd.DataFrame()

            # Get cash flow
            try:
                cash_flow = stock.cashflow
                quarterly_cashflow = stock.quarterly_cashflow
            except:
                cash_flow = pd.DataFrame()
                quarterly_cashflow = pd.DataFrame()

            # Extract key metrics
            data = {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', np.nan),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', np.nan)),

                # Valuation metrics
                'forward_pe': info.get('forwardPE', np.nan),
                'trailing_pe': info.get('trailingPE', np.nan),
                'peg_ratio': info.get('pegRatio', np.nan),
                'price_to_book': info.get('priceToBook', np.nan),
                'price_to_sales': info.get('priceToSalesTrailing12Months', np.nan),
                'ev_to_ebitda': info.get('enterpriseToEbitda', np.nan),
                'ev_to_revenue': info.get('enterpriseToRevenue', np.nan),

                # Profitability metrics
                'profit_margin': info.get('profitMargins', np.nan),
                'operating_margin': info.get('operatingMargins', np.nan),
                'gross_margin': info.get('grossMargins', np.nan),
                'roe': info.get('returnOnEquity', np.nan),
                'roa': info.get('returnOnAssets', np.nan),

                # Financial health
                'debt_to_equity': info.get('debtToEquity', np.nan),
                'current_ratio': info.get('currentRatio', np.nan),
                'quick_ratio': info.get('quickRatio', np.nan),
                'total_debt': info.get('totalDebt', np.nan),
                'total_cash': info.get('totalCash', np.nan),

                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', np.nan),
                'earnings_growth': info.get('earningsGrowth', np.nan),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', np.nan),

                # Cash flow
                'free_cashflow': info.get('freeCashflow', np.nan),
                'operating_cashflow': info.get('operatingCashflow', np.nan),

                # Dividend
                'dividend_yield': info.get('dividendYield', np.nan),
                'payout_ratio': info.get('payoutRatio', np.nan),

                # Price metrics
                'beta': info.get('beta', np.nan),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', np.nan),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', np.nan),
                'fifty_day_average': info.get('fiftyDayAverage', np.nan),
                'two_hundred_day_average': info.get('twoHundredDayAverage', np.nan),

                # EPS
                'trailing_eps': info.get('trailingEps', np.nan),
                'forward_eps': info.get('forwardEps', np.nan),

                # Revenue/Earnings
                'total_revenue': info.get('totalRevenue', np.nan),
                'ebitda': info.get('ebitda', np.nan),
                'net_income': info.get('netIncomeToCommon', np.nan),

                # Analyst targets
                'target_high_price': info.get('targetHighPrice', np.nan),
                'target_low_price': info.get('targetLowPrice', np.nan),
                'target_mean_price': info.get('targetMeanPrice', np.nan),
                'recommendation_mean': info.get('recommendationMean', np.nan),
            }

            return data

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return {'ticker': ticker, 'error': str(e)}

    return {'ticker': ticker, 'error': 'Max retries exceeded'}


def fetch_historical_returns(ticker, period='1y'):
    """Fetch historical price data and calculate returns"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if len(hist) < 20:
            return {'ticker': ticker, '1y_return': np.nan, '6m_return': np.nan,
                    '3m_return': np.nan, '1m_return': np.nan, 'volatility': np.nan}

        returns = hist['Close'].pct_change().dropna()

        data = {
            'ticker': ticker,
            '1y_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) if len(hist) > 200 else np.nan,
            '6m_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[len(hist)//2] - 1) if len(hist) > 100 else np.nan,
            '3m_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[-min(63, len(hist))] - 1) if len(hist) > 63 else np.nan,
            '1m_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[-min(21, len(hist))] - 1) if len(hist) > 21 else np.nan,
            'volatility': returns.std() * np.sqrt(252),
            'sharpe_approx': (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else np.nan
        }

        return data

    except Exception as e:
        return {'ticker': ticker, '1y_return': np.nan, '6m_return': np.nan,
                '3m_return': np.nan, '1m_return': np.nan, 'volatility': np.nan}


def fetch_all_data(tickers_df, sample_size=None, delay=0.1):
    """Fetch all fundamental and return data for given tickers"""
    tickers = tickers_df['ticker'].tolist()

    if sample_size:
        tickers = tickers[:sample_size]

    print(f"\nFetching fundamental data for {len(tickers)} stocks...")

    fundamental_data = []
    returns_data = []

    for ticker in tqdm(tickers, desc="Fetching data"):
        # Fetch fundamental data
        fund_data = fetch_fundamental_data(ticker)
        if 'error' not in fund_data:
            fundamental_data.append(fund_data)

        # Fetch returns data
        ret_data = fetch_historical_returns(ticker)
        returns_data.append(ret_data)

        time.sleep(delay)

    # Create DataFrames
    fund_df = pd.DataFrame(fundamental_data)
    returns_df = pd.DataFrame(returns_data)

    # Merge with original ticker info
    result = tickers_df[tickers_df['ticker'].isin(fund_df['ticker'])].merge(
        fund_df, on='ticker', how='left', suffixes=('_orig', '')
    )

    # Use sector from API if available, otherwise from original
    if 'sector_orig' in result.columns and 'sector' in result.columns:
        result['sector'] = result['sector'].fillna(result['sector_orig'])
        result = result.drop(columns=['sector_orig'])

    # Merge returns
    result = result.merge(returns_df, on='ticker', how='left')

    print(f"\nSuccessfully fetched data for {len(result)} stocks")

    return result


if __name__ == "__main__":
    # Test the fetcher
    tickers = get_combined_tickers()
    print(tickers.head(20))

    # Fetch sample data
    sample_data = fetch_all_data(tickers, sample_size=5)
    print(sample_data)
