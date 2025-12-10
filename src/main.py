#!/usr/bin/env python3
"""
Sector Analysis - Main Runner Script

Comprehensive stock analysis system that:
1. Fetches fundamental data for S&P 500 and Nasdaq stocks
2. Analyzes fundamentals by sector
3. Calculates valuation ratings (5 categories)
4. Performs technical analysis
5. Generates correlation analysis and visualizations
6. Uses OLS and ML models for future performance outlook
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import local modules
from data_fetcher import get_combined_tickers, fetch_all_data
from fundamental_analysis import (
    analyze_fundamentals, get_top_picks_by_sector,
    get_sector_comparison, RATING_CATEGORIES
)
from advanced_metrics import (
    calculate_all_performance_metrics, calculate_all_fundamental_metrics,
    calculate_altman_z_score, calculate_piotroski_f_score,
    calculate_composite_quality_score
)
from technical_analysis import calculate_all_technicals, get_technical_signal
from visualization import create_all_plots
from regression_models import (
    generate_regression_report, predict_future_performance,
    train_ml_models
)
from demo_data import generate_demo_dataset


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        SECTOR ANALYSIS SYSTEM                                ║
║                                                                              ║
║  Comprehensive Stock Fundamental & Technical Analysis                        ║
║  S&P 500 & NASDAQ Stocks | Sector Comparison | Valuation Ratings            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def save_ratings_to_csv(df, output_dir):
    """Save comprehensive stock ratings to CSV"""
    # Select columns for output
    output_cols = [
        'ticker', 'name', 'sector', 'industry',
        'current_price', 'market_cap',

        # Valuation metrics
        'forward_pe', 'trailing_pe', 'peg_ratio', 'price_to_book',
        'price_to_sales', 'ev_to_ebitda',

        # Profitability
        'profit_margin', 'operating_margin', 'gross_margin',
        'roe', 'roa',

        # Financial health
        'debt_to_equity', 'current_ratio', 'quick_ratio',

        # Growth
        'revenue_growth', 'earnings_growth',

        # Cash flow
        'free_cashflow', 'operating_cashflow',

        # Performance
        '1y_return', '3m_return', '1m_return',
        'volatility', 'excess_return',

        # Ratings
        'valuation_score', 'valuation_rating', 'valuation_category',
        'performance_score', 'performance_rating', 'performance_category',
        'combined_score'
    ]

    # Select available columns
    available_cols = [c for c in output_cols if c in df.columns]
    output_df = df[available_cols].copy()

    # Sort by sector and valuation rating
    output_df = output_df.sort_values(['sector', 'valuation_rating'])

    # Save to CSV
    output_path = os.path.join(output_dir, 'stock_ratings.csv')
    output_df.to_csv(output_path, index=False)
    print(f"\nStock ratings saved to: {output_path}")

    return output_df


def save_sector_summary(df, sector_metrics, output_dir):
    """Save sector summary to CSV"""
    summary = get_sector_comparison(df, sector_metrics)
    summary_path = os.path.join(output_dir, 'sector_summary.csv')
    summary.to_csv(summary_path, index=False)
    print(f"Sector summary saved to: {summary_path}")
    return summary


def save_top_picks(df, output_dir, n_picks=10):
    """Save top undervalued picks by sector"""
    picks = get_top_picks_by_sector(df, n=n_picks)

    all_picks = []
    for sector, stocks in picks.items():
        for stock in stocks:
            stock['sector'] = sector
            all_picks.append(stock)

    picks_df = pd.DataFrame(all_picks)
    picks_path = os.path.join(output_dir, 'top_picks_by_sector.csv')
    picks_df.to_csv(picks_path, index=False)
    print(f"Top picks saved to: {picks_path}")

    return picks_df


def print_summary_report(df, sector_metrics):
    """Print summary report to console"""
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY REPORT")
    print("=" * 70)

    print(f"\nTotal stocks analyzed: {len(df)}")
    print(f"Sectors: {df['sector'].nunique()}")

    print("\n" + "-" * 50)
    print("VALUATION DISTRIBUTION")
    print("-" * 50)
    for rating, category in RATING_CATEGORIES.items():
        count = (df['valuation_rating'] == rating).sum()
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"  {category:25s}: {count:4d} ({pct:5.1f}%) {bar}")

    print("\n" + "-" * 50)
    print("SECTOR OVERVIEW")
    print("-" * 50)

    sector_summary = df.groupby('sector').agg({
        'ticker': 'count',
        'market_cap': 'sum',
        '1y_return': 'median',
        'valuation_rating': 'mean'
    }).round(2)

    sector_summary.columns = ['Stocks', 'Market Cap', 'Med 1Y Return', 'Avg Rating']
    sector_summary['Market Cap'] = (sector_summary['Market Cap'] / 1e12).round(2)
    sector_summary['Med 1Y Return'] = (sector_summary['Med 1Y Return'] * 100).round(1)
    sector_summary = sector_summary.sort_values('Market Cap', ascending=False)

    for sector, row in sector_summary.iterrows():
        print(f"\n  {sector}:")
        print(f"    Stocks: {row['Stocks']:.0f} | Market Cap: ${row['Market Cap']:.1f}T")
        print(f"    1Y Return: {row['Med 1Y Return']:+.1f}% | Avg Rating: {row['Avg Rating']:.1f}")

    print("\n" + "-" * 50)
    print("TOP 10 UNDERVALUED STOCKS (Overall)")
    print("-" * 50)

    top_undervalued = df.nsmallest(10, 'valuation_score')[
        ['ticker', 'name', 'sector', 'valuation_score', 'forward_pe',
         'roe', '1y_return', 'valuation_category']
    ]

    for _, row in top_undervalued.iterrows():
        print(f"\n  {row['ticker']:6s} - {row['name'][:30]:30s}")
        print(f"    Sector: {row['sector'][:20]:20s} | P/E: {row['forward_pe']:.1f}")
        print(f"    ROE: {row['roe']*100:.1f}% | 1Y Return: {row['1y_return']*100:+.1f}%")
        print(f"    Rating: {row['valuation_category']}")

    print("\n" + "-" * 50)
    print("TOP 10 OVERVALUED STOCKS (Overall)")
    print("-" * 50)

    top_overvalued = df.nlargest(10, 'valuation_score')[
        ['ticker', 'name', 'sector', 'valuation_score', 'forward_pe',
         'roe', '1y_return', 'valuation_category']
    ]

    for _, row in top_overvalued.iterrows():
        print(f"\n  {row['ticker']:6s} - {row['name'][:30]:30s}")
        print(f"    Sector: {row['sector'][:20]:20s} | P/E: {row['forward_pe']:.1f}")
        print(f"    ROE: {row['roe']*100:.1f}% | 1Y Return: {row['1y_return']*100:+.1f}%")
        print(f"    Rating: {row['valuation_category']}")

    print("\n" + "=" * 70)


def run_analysis(sample_size=None, output_dir='output', skip_plots=False, demo_mode=False):
    """
    Main analysis function

    Args:
        sample_size: Limit number of stocks (for testing). None = all stocks
        output_dir: Directory for output files
        skip_plots: Skip plot generation
        demo_mode: Use simulated data (for testing without internet)
    """
    print_banner()

    start_time = datetime.now()
    print(f"Analysis started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    if demo_mode:
        # Use simulated demo data
        print("\n" + "=" * 50)
        print("DEMO MODE: Using simulated data")
        print("=" * 50)
        df = generate_demo_dataset()
    else:
        # Step 1: Fetch tickers
        print("\n" + "=" * 50)
        print("STEP 1: FETCHING STOCK TICKERS")
        print("=" * 50)
        tickers_df = get_combined_tickers()

        # Step 2: Fetch fundamental data
        print("\n" + "=" * 50)
        print("STEP 2: FETCHING FUNDAMENTAL DATA")
        print("=" * 50)
        df = fetch_all_data(tickers_df, sample_size=sample_size, delay=0.05)

    if len(df) < 10:
        print("ERROR: Insufficient data fetched. Exiting.")
        return None

    # Step 3: Run fundamental analysis
    print("\n" + "=" * 50)
    print("STEP 3: FUNDAMENTAL ANALYSIS")
    print("=" * 50)
    df, sector_metrics = analyze_fundamentals(df)

    # Step 4: Calculate advanced metrics
    print("\n" + "=" * 50)
    print("STEP 4: CALCULATING ADVANCED METRICS")
    print("=" * 50)

    print("Calculating composite quality scores...")
    df['quality_score'] = df.apply(
        lambda row: calculate_composite_quality_score(row.to_dict()),
        axis=1
    )

    # Step 5: Generate regression analysis
    print("\n" + "=" * 50)
    print("STEP 5: REGRESSION ANALYSIS")
    print("=" * 50)
    regression_report, ols_model, sector_models, ml_results = generate_regression_report(
        df, output_path=os.path.join(output_dir, 'regression_report.txt')
    )
    print(regression_report)

    # Step 6: Generate predictions
    print("\n" + "=" * 50)
    print("STEP 6: GENERATING PREDICTIONS")
    print("=" * 50)

    if ml_results is not None:
        features = ['forward_pe', 'price_to_book', 'debt_to_equity', 'roe',
                    'profit_margin', 'revenue_growth', 'volatility', 'beta']
        features = [f for f in features if f in df.columns]

        df_pred, best_model = predict_future_performance(df, ml_results, features)
        print(f"Predictions generated using {best_model} model")
        df = df_pred

    # Step 7: Generate visualizations
    if not skip_plots:
        print("\n" + "=" * 50)
        print("STEP 7: GENERATING VISUALIZATIONS")
        print("=" * 50)
        create_all_plots(df, sector_metrics, output_dir)

    # Step 8: Save outputs
    print("\n" + "=" * 50)
    print("STEP 8: SAVING OUTPUTS")
    print("=" * 50)

    save_ratings_to_csv(df, output_dir)
    save_sector_summary(df, sector_metrics, output_dir)
    save_top_picks(df, output_dir)

    # Print summary report
    print_summary_report(df, sector_metrics)

    # Finish
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Duration: {duration:.1f} seconds")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print("\nFiles generated:")
    for f in os.listdir(output_dir):
        size = os.path.getsize(os.path.join(output_dir, f)) / 1024
        print(f"  - {f} ({size:.1f} KB)")

    return df, sector_metrics


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Sector Analysis System - Comprehensive Stock Analysis'
    )
    parser.add_argument(
        '--sample', '-s', type=int, default=None,
        help='Sample size (number of stocks). Default: all stocks'
    )
    parser.add_argument(
        '--output', '-o', type=str, default='output',
        help='Output directory. Default: output'
    )
    parser.add_argument(
        '--skip-plots', action='store_true',
        help='Skip plot generation'
    )
    parser.add_argument(
        '--demo', '-d', action='store_true',
        help='Use demo data (simulated data for testing without internet)'
    )

    args = parser.parse_args()

    run_analysis(
        sample_size=args.sample,
        output_dir=args.output,
        skip_plots=args.skip_plots,
        demo_mode=args.demo
    )


if __name__ == "__main__":
    main()
