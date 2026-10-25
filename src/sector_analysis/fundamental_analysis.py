"""
Fundamental Analysis Engine
Analyzes stocks by sector and creates valuation ratings
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# GICS Sectors mapping
GICS_SECTORS = {
    'Communication Services': 'Communication Services',
    'Consumer Discretionary': 'Consumer Discretionary',
    'Consumer Staples': 'Consumer Staples',
    'Energy': 'Energy',
    'Financials': 'Financials',
    'Health Care': 'Health Care',
    'Healthcare': 'Health Care',
    'Industrials': 'Industrials',
    'Information Technology': 'Technology',
    'Technology': 'Technology',
    'Materials': 'Materials',
    'Real Estate': 'Real Estate',
    'Utilities': 'Utilities',
    'Basic Materials': 'Materials',
}

# Rating categories
RATING_CATEGORIES = {
    1: 'Strongly Undervalued',
    2: 'Undervalued',
    3: 'Fairly Valued',
    4: 'Overvalued',
    5: 'Strongly Overvalued'
}


def normalize_sector(sector):
    """Normalize sector names to standard GICS sectors"""
    if pd.isna(sector):
        return 'Unknown'
    return GICS_SECTORS.get(sector, sector)


def calculate_sector_metrics(df):
    """Calculate sector-level metrics for comparison"""
    sector_metrics = df.groupby('sector').agg({
        'forward_pe': ['mean', 'median', 'std'],
        'price_to_book': ['mean', 'median', 'std'],
        'debt_to_equity': ['mean', 'median', 'std'],
        'profit_margin': ['mean', 'median', 'std'],
        'roe': ['mean', 'median', 'std'],
        'revenue_growth': ['mean', 'median', 'std'],
        'free_cashflow': ['mean', 'median', 'std'],
        '1y_return': ['mean', 'median', 'std'],
        'market_cap': ['mean', 'median', 'count']
    }).round(4)

    sector_metrics.columns = ['_'.join(col).strip() for col in sector_metrics.columns.values]
    return sector_metrics


def calculate_excess_return(df, sector_metrics):
    """Calculate excess return relative to sector average"""
    df = df.copy()
    df['sector_avg_return'] = df['sector'].map(
        sector_metrics['1y_return_mean'].to_dict()
    )
    df['excess_return'] = df['1y_return'] - df['sector_avg_return']
    return df


def calculate_relative_metrics(df, sector_metrics):
    """Calculate metrics relative to sector averages"""
    df = df.copy()

    # Forward P/E relative to sector
    sector_pe = sector_metrics['forward_pe_median'].to_dict()
    df['sector_forward_pe'] = df['sector'].map(sector_pe)
    df['relative_forward_pe'] = df['forward_pe'] / df['sector_forward_pe']

    # P/B relative to sector
    sector_pb = sector_metrics['price_to_book_median'].to_dict()
    df['sector_price_to_book'] = df['sector'].map(sector_pb)
    df['relative_price_to_book'] = df['price_to_book'] / df['sector_price_to_book']

    # D/E relative to sector
    sector_de = sector_metrics['debt_to_equity_median'].to_dict()
    df['sector_debt_to_equity'] = df['sector'].map(sector_de)
    df['relative_debt_to_equity'] = df['debt_to_equity'] / df['sector_debt_to_equity']

    # ROE relative to sector
    sector_roe = sector_metrics['roe_median'].to_dict()
    df['sector_roe'] = df['sector'].map(sector_roe)
    df['relative_roe'] = df['roe'] / df['sector_roe']

    return df


def calculate_valuation_score(row):
    """
    Calculate a composite valuation score (lower = more undervalued)
    Score components:
    - Forward P/E (lower is better for value)
    - Price to Book (lower is better)
    - Debt to Equity (lower is better)
    - Free Cash Flow Yield (higher is better - inverse)
    - ROE (higher is better - inverse)
    - Profit Margin (higher is better - inverse)
    """
    scores = []
    weights = []

    # Forward P/E (30% weight)
    if pd.notna(row.get('relative_forward_pe')) and row['relative_forward_pe'] > 0:
        scores.append(min(row['relative_forward_pe'], 3))  # Cap at 3x sector
        weights.append(0.30)

    # Price to Book (20% weight)
    if pd.notna(row.get('relative_price_to_book')) and row['relative_price_to_book'] > 0:
        scores.append(min(row['relative_price_to_book'], 3))
        weights.append(0.20)

    # Debt to Equity (15% weight)
    if pd.notna(row.get('relative_debt_to_equity')) and row['relative_debt_to_equity'] >= 0:
        scores.append(min(row['relative_debt_to_equity'], 3))
        weights.append(0.15)

    # ROE (inverse - 15% weight, higher ROE = lower score = more undervalued)
    if pd.notna(row.get('relative_roe')) and row['relative_roe'] > 0:
        inverse_roe = 1 / min(row['relative_roe'], 3)
        scores.append(inverse_roe)
        weights.append(0.15)

    # Free Cash Flow Yield proxy (10% weight)
    if pd.notna(row.get('free_cashflow')) and pd.notna(row.get('market_cap')) and row['market_cap'] > 0:
        fcf_yield = row['free_cashflow'] / row['market_cap']
        # Higher FCF yield = more undervalued = lower score
        fcf_score = 1 - min(max(fcf_yield, -0.2), 0.2) * 2.5
        scores.append(fcf_score)
        weights.append(0.10)

    # Profit Margin relative (10% weight)
    if pd.notna(row.get('profit_margin')) and pd.notna(row.get('sector_profit_margin')):
        if row['sector_profit_margin'] > 0:
            rel_margin = row['profit_margin'] / row['sector_profit_margin']
            inverse_margin = 1 / min(max(rel_margin, 0.1), 3)
            scores.append(inverse_margin)
            weights.append(0.10)

    if len(scores) >= 3:
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        return weighted_score
    else:
        return np.nan


def assign_valuation_rating(score, quintiles):
    """Assign valuation rating based on quintiles"""
    if pd.isna(score):
        return np.nan

    for i, q in enumerate(quintiles):
        if score <= q:
            return i + 1
    return 5


def calculate_performance_rating(row, sector_metrics):
    """
    Calculate performance rating (1-5, where 1 = best performer)
    Based on:
    - Excess return to sector
    - Momentum indicators
    - Growth metrics
    """
    scores = []
    weights = []

    # Excess return (40% weight) - higher is better, so we invert
    if pd.notna(row.get('excess_return')):
        # Normalize to 0-1 range roughly, then invert
        excess_normalized = max(min(row['excess_return'], 0.5), -0.5) / 0.5  # -1 to 1
        excess_score = 1 - (excess_normalized + 1) / 2  # 0 to 1, lower = better performance
        scores.append(excess_score)
        weights.append(0.40)

    # Revenue growth (20% weight)
    if pd.notna(row.get('revenue_growth')):
        growth_normalized = max(min(row['revenue_growth'], 0.5), -0.3)
        growth_score = 1 - (growth_normalized + 0.3) / 0.8
        scores.append(growth_score)
        weights.append(0.20)

    # ROE (20% weight)
    if pd.notna(row.get('roe')):
        roe_normalized = max(min(row['roe'], 0.4), -0.1)
        roe_score = 1 - (roe_normalized + 0.1) / 0.5
        scores.append(roe_score)
        weights.append(0.20)

    # Momentum - price vs 200 day average (20% weight)
    if pd.notna(row.get('current_price')) and pd.notna(row.get('two_hundred_day_average')):
        if row['two_hundred_day_average'] > 0:
            momentum = row['current_price'] / row['two_hundred_day_average'] - 1
            momentum_normalized = max(min(momentum, 0.3), -0.3)
            momentum_score = 1 - (momentum_normalized + 0.3) / 0.6
            scores.append(momentum_score)
            weights.append(0.20)

    if len(scores) >= 2:
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        return weighted_score
    else:
        return np.nan


def analyze_fundamentals(df):
    """Main analysis function"""
    print("\n" + "="*60)
    print("FUNDAMENTAL ANALYSIS ENGINE")
    print("="*60)

    # Normalize sectors
    df = df.copy()
    df['sector'] = df['sector'].apply(normalize_sector)

    # Remove stocks with missing critical data
    initial_count = len(df)
    df = df[df['sector'] != 'Unknown']
    print(f"\nFiltered out {initial_count - len(df)} stocks with unknown sector")

    # Calculate sector metrics
    print("\nCalculating sector metrics...")
    sector_metrics = calculate_sector_metrics(df)

    # Add sector profit margin for calculations
    df['sector_profit_margin'] = df['sector'].map(
        sector_metrics['profit_margin_median'].to_dict()
    )

    # Calculate excess returns
    print("Calculating excess returns...")
    df = calculate_excess_return(df, sector_metrics)

    # Calculate relative metrics
    print("Calculating relative metrics...")
    df = calculate_relative_metrics(df, sector_metrics)

    # Calculate valuation scores
    print("Calculating valuation scores...")
    df['valuation_score'] = df.apply(calculate_valuation_score, axis=1)

    # Calculate quintiles for rating assignment
    valid_scores = df['valuation_score'].dropna()
    if len(valid_scores) > 10:
        quintiles = [valid_scores.quantile(q) for q in [0.2, 0.4, 0.6, 0.8]]
        df['valuation_rating'] = df['valuation_score'].apply(
            lambda x: assign_valuation_rating(x, quintiles)
        )
    else:
        df['valuation_rating'] = np.nan

    # Calculate performance scores
    print("Calculating performance scores...")
    df['performance_score'] = df.apply(
        lambda row: calculate_performance_rating(row, sector_metrics), axis=1
    )

    # Performance rating
    valid_perf = df['performance_score'].dropna()
    if len(valid_perf) > 10:
        perf_quintiles = [valid_perf.quantile(q) for q in [0.2, 0.4, 0.6, 0.8]]
        df['performance_rating'] = df['performance_score'].apply(
            lambda x: assign_valuation_rating(x, perf_quintiles)
        )
    else:
        df['performance_rating'] = np.nan

    # Map ratings to categories
    df['valuation_category'] = df['valuation_rating'].map(RATING_CATEGORIES)
    df['performance_category'] = df['performance_rating'].map({
        1: 'Strong Outperformer',
        2: 'Outperformer',
        3: 'Market Performer',
        4: 'Underperformer',
        5: 'Strong Underperformer'
    })

    # Combined score (for overall rating)
    df['combined_score'] = (
        df['valuation_rating'].fillna(3) * 0.5 +
        df['performance_rating'].fillna(3) * 0.5
    )

    # Summary statistics
    print("\n" + "-"*60)
    print("ANALYSIS SUMMARY")
    print("-"*60)

    print(f"\nTotal stocks analyzed: {len(df)}")
    print(f"Sectors identified: {df['sector'].nunique()}")

    print("\nStocks by Sector:")
    sector_counts = df['sector'].value_counts()
    for sector, count in sector_counts.items():
        print(f"  {sector}: {count}")

    print("\nValuation Rating Distribution:")
    val_dist = df['valuation_category'].value_counts().sort_index()
    for cat, count in val_dist.items():
        print(f"  {cat}: {count}")

    return df, sector_metrics


def get_top_picks_by_sector(df, n=5):
    """Get top undervalued stocks by sector"""
    top_picks = {}

    for sector in df['sector'].unique():
        sector_df = df[df['sector'] == sector].copy()
        sector_df = sector_df.sort_values('valuation_score')

        top_picks[sector] = sector_df.head(n)[
            ['ticker', 'name', 'valuation_score', 'valuation_category',
             'forward_pe', 'price_to_book', 'roe', 'excess_return']
        ].to_dict('records')

    return top_picks


def get_sector_comparison(df, sector_metrics):
    """Create sector comparison summary"""
    sectors = df['sector'].unique()

    comparison = []
    for sector in sectors:
        sector_df = df[df['sector'] == sector]
        comparison.append({
            'sector': sector,
            'count': len(sector_df),
            'avg_forward_pe': sector_df['forward_pe'].median(),
            'avg_price_to_book': sector_df['price_to_book'].median(),
            'avg_debt_to_equity': sector_df['debt_to_equity'].median(),
            'avg_roe': sector_df['roe'].median(),
            'avg_1y_return': sector_df['1y_return'].median(),
            'avg_excess_return': sector_df['excess_return'].median(),
            'pct_undervalued': (sector_df['valuation_rating'] <= 2).mean() * 100,
            'pct_overvalued': (sector_df['valuation_rating'] >= 4).mean() * 100,
        })

    return pd.DataFrame(comparison).sort_values('avg_1y_return', ascending=False)


if __name__ == "__main__":
    # Test with sample data
    print("Testing fundamental analysis module...")
