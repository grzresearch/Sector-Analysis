#!/usr/bin/env python3
"""
Sector Analysis - Main Runner Script
=====================================

Comprehensive stock analysis system covering S&P 500 and NASDAQ 100 stocks.

Features:
1. Complete index coverage (503 S&P 500 + 101 NASDAQ 100 stocks)
2. 150+ financial metrics across multiple categories
3. Price & Performance metrics (Sharpe, Sortino, Drawdown, etc.)
4. Fundamental valuation analysis
5. Technical indicators and sentiment analysis
6. Composite quality scores (Altman Z, Piotroski F, Beneish M)
7. Sector-relative comparisons
8. Machine learning predictions
9. Comprehensive visualizations
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
from data_fetcher import get_combined_tickers, fetch_all_data, fetch_market_data
from fundamental_analysis import (
    analyze_fundamentals, get_top_picks_by_sector,
    get_sector_comparison, RATING_CATEGORIES
)
from advanced_metrics import (
    calculate_all_performance_metrics, calculate_all_fundamental_metrics,
    calculate_altman_z_score, calculate_piotroski_f_score,
    calculate_composite_quality_score
)
from comprehensive_metrics import (
    PerformanceMetrics, RelativePerformanceMetrics,
    CompositeScores, calculate_all_metrics,
    calculate_sector_percentiles, calculate_sector_relative
)
from technical_analysis import (
    calculate_all_technicals, get_technical_signal,
    calculate_seasonality, calculate_fear_greed_indicators
)
from visualization import create_all_plots, create_comprehensive_plots
from regression_models import (
    generate_regression_report, predict_future_performance,
    train_ml_models
)
from demo_data import generate_demo_dataset


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMPREHENSIVE SECTOR ANALYSIS SYSTEM                      ║
║                                                                              ║
║  Complete S&P 500 & NASDAQ 100 Analysis | 150+ Metrics | 11 Sectors         ║
║  Fundamental | Technical | Performance | Quality Scores | ML Predictions     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def calculate_extended_metrics(df, price_histories=None, benchmark_data=None):
    """
    Calculate all extended metrics for the dataframe

    Includes:
    - Performance metrics (Sharpe, Sortino, Calmar, Max Drawdown)
    - Relative metrics (Alpha, Beta, Tracking Error, Information Ratio)
    - Composite scores (Altman Z, Piotroski F, Quality Score)
    - Technical signals
    """
    print("  Calculating extended performance metrics...")

    # Calculate metrics for each stock
    extended_data = []

    for idx, row in df.iterrows():
        ticker = row['ticker']
        stock_data = row.to_dict()

        # Get price history if available
        price_history = None
        if price_histories and ticker in price_histories:
            price_history = price_histories[ticker]

        # Get benchmark data
        bench_data = None
        if benchmark_data and 'SPY' in benchmark_data:
            bench_data = benchmark_data['SPY']

        # Calculate comprehensive metrics
        metrics = calculate_all_metrics(
            stock_data,
            price_history=price_history,
            benchmark_data=bench_data
        )

        metrics['ticker'] = ticker
        extended_data.append(metrics)

    # Merge extended metrics back to dataframe
    if extended_data:
        ext_df = pd.DataFrame(extended_data)
        df = df.merge(ext_df, on='ticker', how='left', suffixes=('', '_ext'))

        # Handle duplicate columns
        for col in df.columns:
            if col.endswith('_ext'):
                base_col = col[:-4]
                if base_col in df.columns:
                    df[base_col] = df[base_col].fillna(df[col])
                else:
                    df[base_col] = df[col]
                df = df.drop(columns=[col])

    return df


def calculate_technical_indicators(df, price_histories):
    """Calculate technical indicators for all stocks"""
    print("  Calculating technical indicators...")

    tech_data = []
    for ticker in df['ticker'].unique():
        if ticker in price_histories:
            ohlcv = price_histories[ticker]
            technicals = calculate_all_technicals(ohlcv)
            technicals['ticker'] = ticker

            # Get technical signal
            signal, score = get_technical_signal(technicals)
            technicals['technical_signal'] = signal
            technicals['technical_score'] = score

            tech_data.append(technicals)

    if tech_data:
        tech_df = pd.DataFrame(tech_data)

        # Select key technical columns
        tech_cols = [
            'ticker', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
            'bb_percent_b', 'bb_bandwidth', 'sma_50', 'sma_200',
            'price_vs_sma_200', 'golden_cross', 'support', 'resistance',
            'atr', 'atr_percent', 'stoch_k', 'stoch_d', 'adx',
            'volume_ratio', 'vwap', 'mfi', 'obv', 'cmf',
            'technical_signal', 'technical_score'
        ]
        tech_cols = [c for c in tech_cols if c in tech_df.columns]

        df = df.merge(tech_df[tech_cols], on='ticker', how='left')

    return df


def calculate_quality_scores(df):
    """Calculate composite quality scores"""
    print("  Calculating composite quality scores...")

    # Altman Z-Score
    def calc_z_score(row):
        try:
            return CompositeScores.altman_z_score(
                row.get('working_capital'),
                row.get('total_assets'),
                row.get('retained_earnings'),
                row.get('ebit'),
                row.get('market_cap'),
                row.get('total_liabilities'),
                row.get('total_revenue')
            )
        except:
            return np.nan

    df['altman_z_score'] = df.apply(calc_z_score, axis=1)
    df['z_score_zone'] = df['altman_z_score'].apply(CompositeScores.interpret_z_score)

    # Piotroski F-Score
    def calc_f_score(row):
        try:
            data = {
                'roa': row.get('roa', 0),
                'operating_cashflow': row.get('operating_cashflow', 0),
                'net_income': row.get('net_income', 0),
                'roa_change': 0,  # Would need historical data
                'debt_to_equity_change': 0,
                'current_ratio_change': 0,
                'shares_change': 0,
                'gross_margin_change': 0,
                'asset_turnover_change': 0
            }
            return CompositeScores.piotroski_f_score(data)
        except:
            return np.nan

    df['piotroski_f_score'] = df.apply(calc_f_score, axis=1)
    df['f_score_interpretation'] = df['piotroski_f_score'].apply(CompositeScores.interpret_f_score)

    # Quality Score
    def calc_quality(row):
        try:
            return CompositeScores.quality_score(row.to_dict())
        except:
            return np.nan

    df['quality_score'] = df.apply(calc_quality, axis=1)

    return df


def calculate_sector_metrics(df):
    """Calculate sector-relative metrics"""
    print("  Calculating sector-relative metrics...")

    # Metrics for percentile calculation
    metrics_for_percentile = [
        'forward_pe', 'price_to_book', 'ev_to_ebitda', 'roe', 'roa',
        'profit_margin', 'revenue_growth', 'debt_to_equity', '1y_return',
        'volatility', 'sharpe_approx', 'quality_score'
    ]
    metrics_for_percentile = [m for m in metrics_for_percentile if m in df.columns]

    # Calculate percentiles
    df = calculate_sector_percentiles(df, metrics_for_percentile)

    # Calculate vs sector median
    metrics_for_relative = ['forward_pe', 'price_to_book', 'roe', 'profit_margin']
    metrics_for_relative = [m for m in metrics_for_relative if m in df.columns]
    df = calculate_sector_relative(df, metrics_for_relative)

    return df


def save_ratings_to_csv(df, output_dir):
    """Save comprehensive stock ratings to CSV"""
    # Select columns for output
    output_cols = [
        'ticker', 'name', 'sector', 'industry',
        'current_price', 'market_cap',

        # Valuation metrics
        'forward_pe', 'trailing_pe', 'peg_ratio', 'price_to_book',
        'price_to_sales', 'ev_to_ebitda', 'ev_to_revenue',

        # Profitability
        'profit_margin', 'operating_margin', 'gross_margin', 'ebitda_margin',
        'roe', 'roa', 'roic',

        # Financial health
        'debt_to_equity', 'current_ratio', 'quick_ratio',
        'net_debt_to_ebitda', 'interest_coverage',

        # Growth
        'revenue_growth', 'earnings_growth',

        # Cash flow
        'free_cashflow', 'operating_cashflow', 'fcf_yield',

        # Performance
        '1y_return', '6m_return', '3m_return', '1m_return',
        'volatility', 'sharpe_approx', 'max_drawdown',
        'excess_return', 'alpha', 'beta',

        # Quality scores
        'altman_z_score', 'z_score_zone',
        'piotroski_f_score', 'f_score_interpretation',
        'quality_score',

        # Technical
        'rsi', 'macd', 'bb_percent_b', 'adx',
        'technical_signal', 'technical_score',

        # Ratings
        'valuation_score', 'valuation_rating', 'valuation_category',
        'performance_score', 'performance_rating', 'performance_category',
        'combined_score',

        # Sector relative
        'forward_pe_sector_percentile', 'roe_sector_percentile',
        'quality_score_sector_percentile'
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

    # Quality Scores Summary
    print("\n" + "-" * 50)
    print("QUALITY SCORES SUMMARY")
    print("-" * 50)

    if 'altman_z_score' in df.columns:
        z_safe = (df['z_score_zone'] == 'Safe Zone').sum()
        z_grey = (df['z_score_zone'] == 'Grey Zone').sum()
        z_distress = (df['z_score_zone'] == 'Distress Zone').sum()
        print(f"  Altman Z-Score: Safe: {z_safe} | Grey: {z_grey} | Distress: {z_distress}")

    if 'piotroski_f_score' in df.columns:
        f_strong = (df['piotroski_f_score'] >= 7).sum()
        f_weak = (df['piotroski_f_score'] <= 3).sum()
        print(f"  Piotroski F-Score: Strong (>=7): {f_strong} | Weak (<=3): {f_weak}")

    if 'quality_score' in df.columns:
        print(f"  Quality Score: Median: {df['quality_score'].median():.1f} | "
              f"Top Quartile: {df['quality_score'].quantile(0.75):.1f}")

    # Technical Summary
    if 'technical_signal' in df.columns:
        print("\n" + "-" * 50)
        print("TECHNICAL SIGNALS SUMMARY")
        print("-" * 50)
        signals = df['technical_signal'].value_counts()
        for signal, count in signals.items():
            print(f"  {signal}: {count} stocks")

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

    cols_to_show = ['ticker', 'name', 'sector', 'valuation_score', 'forward_pe',
                    'roe', '1y_return', 'valuation_category']
    cols_to_show = [c for c in cols_to_show if c in df.columns]

    top_undervalued = df.nsmallest(10, 'valuation_score')[cols_to_show]

    for _, row in top_undervalued.iterrows():
        print(f"\n  {row['ticker']:6s} - {str(row.get('name', ''))[:30]:30s}")
        print(f"    Sector: {str(row.get('sector', ''))[:20]:20s} | P/E: {row.get('forward_pe', 0):.1f}")
        roe_val = row.get('roe', 0)
        ret_val = row.get('1y_return', 0)
        if pd.notna(roe_val) and pd.notna(ret_val):
            print(f"    ROE: {roe_val*100:.1f}% | 1Y Return: {ret_val*100:+.1f}%")
        print(f"    Rating: {row.get('valuation_category', 'N/A')}")

    print("\n" + "=" * 70)


def run_analysis(sample_size=None, output_dir='output', skip_plots=False,
                 demo_mode=False, comprehensive=True):
    """
    Main analysis function

    Args:
        sample_size: Limit number of stocks (for testing). None = all stocks
        output_dir: Directory for output files
        skip_plots: Skip plot generation
        demo_mode: Use simulated data (for testing without internet)
        comprehensive: Run comprehensive analysis with all metrics
    """
    print_banner()

    start_time = datetime.now()
    print(f"Analysis started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    price_histories = {}

    if demo_mode:
        # Use simulated demo data
        print("\n" + "=" * 50)
        print("DEMO MODE: Using simulated data")
        print("=" * 50)
        df = generate_demo_dataset()
        benchmark_data = None
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
        df, price_histories = fetch_all_data(tickers_df, sample_size=sample_size, delay=0.05)

        # Fetch benchmark data for relative metrics
        print("\n  Fetching benchmark data...")
        benchmark_data = fetch_market_data()

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

    if comprehensive:
        # Extended performance metrics
        df = calculate_extended_metrics(df, price_histories, benchmark_data)

        # Technical indicators
        if price_histories:
            df = calculate_technical_indicators(df, price_histories)

        # Quality scores
        df = calculate_quality_scores(df)

        # Sector-relative metrics
        df = calculate_sector_metrics(df)
    else:
        # Basic quality score only
        print("  Calculating basic quality scores...")
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

        if comprehensive:
            create_comprehensive_plots(df, sector_metrics, output_dir)
        else:
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
    for f in sorted(os.listdir(output_dir)):
        size = os.path.getsize(os.path.join(output_dir, f)) / 1024
        print(f"  - {f} ({size:.1f} KB)")

    return df, sector_metrics


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Comprehensive Sector Analysis System - S&P 500 & NASDAQ 100'
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
    parser.add_argument(
        '--basic', '-b', action='store_true',
        help='Run basic analysis only (faster, fewer metrics)'
    )

    args = parser.parse_args()

    run_analysis(
        sample_size=args.sample,
        output_dir=args.output,
        skip_plots=args.skip_plots,
        demo_mode=args.demo,
        comprehensive=not args.basic
    )


if __name__ == "__main__":
    main()
