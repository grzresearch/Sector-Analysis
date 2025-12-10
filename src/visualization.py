"""
Visualization Module
Comprehensive plotting functions for sector analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def setup_plot_style():
    """Setup consistent plot styling"""
    plt.rcParams['figure.figsize'] = (14, 10)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['figure.dpi'] = 100


# =============================================================================
# SECTOR ANALYSIS PLOTS
# =============================================================================

def plot_sector_heatmap(df, metrics, title="Sector Metrics Heatmap", save_path=None):
    """
    Create heatmap comparing metrics across sectors
    """
    setup_plot_style()

    # Prepare data
    sector_data = df.groupby('sector')[metrics].median()

    # Normalize for heatmap
    normalized = (sector_data - sector_data.min()) / (sector_data.max() - sector_data.min())

    fig, ax = plt.subplots(figsize=(14, 8))

    # Create heatmap
    sns.heatmap(normalized, annot=sector_data.round(2), fmt='', cmap='RdYlGn_r',
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Relative Scale (0-1)'})

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Metrics', fontsize=11)
    ax.set_ylabel('Sector', fontsize=11)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_sector_comparison(df, save_path=None):
    """
    Create comprehensive sector comparison dashboard
    """
    setup_plot_style()
    fig = plt.figure(figsize=(18, 14))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

    sectors = df['sector'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(sectors)))
    sector_colors = dict(zip(sectors, colors))

    # 1. Sector market cap distribution (bar)
    ax1 = fig.add_subplot(gs[0, 0])
    sector_mcap = df.groupby('sector')['market_cap'].sum().sort_values(ascending=True) / 1e12
    sector_mcap.plot(kind='barh', ax=ax1, color=[sector_colors[s] for s in sector_mcap.index])
    ax1.set_title('Total Market Cap by Sector ($T)', fontweight='bold')
    ax1.set_xlabel('Market Cap (Trillion $)')

    # 2. Average Forward P/E by sector
    ax2 = fig.add_subplot(gs[0, 1])
    sector_pe = df.groupby('sector')['forward_pe'].median().sort_values()
    sector_pe.plot(kind='barh', ax=ax2, color=[sector_colors[s] for s in sector_pe.index])
    ax2.set_title('Median Forward P/E by Sector', fontweight='bold')
    ax2.axvline(x=df['forward_pe'].median(), color='red', linestyle='--', label='Market Median')
    ax2.legend()

    # 3. Average ROE by sector
    ax3 = fig.add_subplot(gs[0, 2])
    sector_roe = df.groupby('sector')['roe'].median().sort_values(ascending=True) * 100
    colors_roe = ['green' if x > 0 else 'red' for x in sector_roe]
    sector_roe.plot(kind='barh', ax=ax3, color=colors_roe)
    ax3.set_title('Median ROE by Sector (%)', fontweight='bold')
    ax3.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    # 4. 1Y Return distribution by sector (box plot)
    ax4 = fig.add_subplot(gs[1, :2])
    df_plot = df[df['1y_return'].notna()].copy()
    df_plot['1y_return_pct'] = df_plot['1y_return'] * 100
    order = df_plot.groupby('sector')['1y_return_pct'].median().sort_values(ascending=False).index
    sns.boxplot(data=df_plot, x='sector', y='1y_return_pct', order=order, ax=ax4, palette='coolwarm')
    ax4.set_title('1-Year Return Distribution by Sector', fontweight='bold')
    ax4.set_xlabel('')
    ax4.set_ylabel('1Y Return (%)')
    ax4.tick_params(axis='x', rotation=45)
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    # 5. Valuation rating distribution by sector
    ax5 = fig.add_subplot(gs[1, 2])
    rating_counts = df.groupby(['sector', 'valuation_rating']).size().unstack(fill_value=0)
    rating_counts_pct = rating_counts.div(rating_counts.sum(axis=1), axis=0) * 100
    rating_counts_pct.plot(kind='bar', stacked=True, ax=ax5,
                           colormap='RdYlGn_r', edgecolor='white')
    ax5.set_title('Valuation Distribution by Sector', fontweight='bold')
    ax5.set_xlabel('')
    ax5.set_ylabel('Percentage')
    ax5.tick_params(axis='x', rotation=45)
    ax5.legend(title='Rating', labels=['Undervalued', '', 'Fair', '', 'Overvalued'],
               loc='upper right')

    # 6. Debt to Equity by sector
    ax6 = fig.add_subplot(gs[2, 0])
    sector_de = df.groupby('sector')['debt_to_equity'].median().sort_values()
    colors_de = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(sector_de)))
    sector_de.plot(kind='barh', ax=ax6, color=colors_de)
    ax6.set_title('Median Debt/Equity by Sector', fontweight='bold')

    # 7. Free Cash Flow Yield by sector
    ax7 = fig.add_subplot(gs[2, 1])
    df['fcf_yield'] = df['free_cashflow'] / df['market_cap']
    sector_fcf = df.groupby('sector')['fcf_yield'].median().sort_values(ascending=True) * 100
    colors_fcf = ['green' if x > 0 else 'red' for x in sector_fcf]
    sector_fcf.plot(kind='barh', ax=ax7, color=colors_fcf)
    ax7.set_title('Median FCF Yield by Sector (%)', fontweight='bold')
    ax7.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    # 8. Number of stocks by sector
    ax8 = fig.add_subplot(gs[2, 2])
    sector_counts = df['sector'].value_counts()
    ax8.pie(sector_counts, labels=sector_counts.index, autopct='%1.0f%%',
            colors=[sector_colors[s] for s in sector_counts.index])
    ax8.set_title('Stock Distribution by Sector', fontweight='bold')

    plt.suptitle('Comprehensive Sector Comparison Dashboard', fontsize=16, fontweight='bold', y=1.02)

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


# =============================================================================
# CORRELATION ANALYSIS PLOTS
# =============================================================================

def plot_correlation_matrix(df, metrics, title="Correlation Matrix", save_path=None):
    """Plot correlation matrix for selected metrics"""
    setup_plot_style()

    corr = df[metrics].corr()

    fig, ax = plt.subplots(figsize=(12, 10))

    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, linewidths=0.5, ax=ax,
                vmin=-1, vmax=1)

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_sector_correlations(df, save_path=None):
    """Plot excess returns correlation with fundamental metrics by sector"""
    setup_plot_style()

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    metrics = [
        ('forward_pe', 'Forward P/E'),
        ('free_cashflow', 'Free Cash Flow'),
        ('debt_to_equity', 'Debt/Equity'),
        ('roe', 'ROE')
    ]

    for ax, (metric, label) in zip(axes.flat, metrics):
        for sector in df['sector'].unique():
            sector_df = df[df['sector'] == sector]
            valid_data = sector_df[[metric, 'excess_return']].dropna()
            if len(valid_data) > 5:
                ax.scatter(valid_data[metric], valid_data['excess_return'] * 100,
                          alpha=0.6, label=sector, s=30)

        ax.set_xlabel(label)
        ax.set_ylabel('Excess Return vs Sector (%)')
        ax.set_title(f'Excess Return vs {label}', fontweight='bold')
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right', bbox_to_anchor=(1.15, 0.5))

    plt.suptitle('Sector Excess Returns Correlation Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


# =============================================================================
# RISK-RETURN ANALYSIS PLOTS
# =============================================================================

def plot_risk_return_scatter(df, save_path=None):
    """
    Create risk-return scatter plot by sector
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=(14, 10))

    sectors = df['sector'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(sectors)))

    for sector, color in zip(sectors, colors):
        sector_df = df[df['sector'] == sector]
        valid_data = sector_df[['volatility', '1y_return', 'market_cap']].dropna()

        if len(valid_data) > 0:
            sizes = np.sqrt(valid_data['market_cap'] / 1e9) * 3
            ax.scatter(valid_data['volatility'] * 100,
                      valid_data['1y_return'] * 100,
                      s=sizes, alpha=0.6, label=sector, c=[color])

    ax.set_xlabel('Annualized Volatility (%)', fontsize=12)
    ax.set_ylabel('1-Year Return (%)', fontsize=12)
    ax.set_title('Risk-Return Analysis by Sector\n(Bubble size = Market Cap)', fontsize=14, fontweight='bold')
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


# =============================================================================
# VALUATION DISTRIBUTION PLOTS
# =============================================================================

def plot_valuation_distribution(df, save_path=None):
    """Plot valuation score distribution with rating categories"""
    setup_plot_style()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Overall valuation score histogram
    ax1 = axes[0, 0]
    df['valuation_score'].hist(bins=30, ax=ax1, color='steelblue', edgecolor='white', alpha=0.7)
    ax1.set_title('Valuation Score Distribution', fontweight='bold')
    ax1.set_xlabel('Valuation Score (lower = more undervalued)')
    ax1.set_ylabel('Frequency')

    # Add quintile lines
    quintiles = df['valuation_score'].quantile([0.2, 0.4, 0.6, 0.8])
    for q, val in quintiles.items():
        ax1.axvline(x=val, color='red', linestyle='--', alpha=0.7)

    # 2. Rating category counts
    ax2 = axes[0, 1]
    rating_counts = df['valuation_category'].value_counts()
    order = ['Strongly Undervalued', 'Undervalued', 'Fairly Valued', 'Overvalued', 'Strongly Overvalued']
    rating_counts = rating_counts.reindex([c for c in order if c in rating_counts.index])
    colors = ['darkgreen', 'lightgreen', 'gold', 'orange', 'red'][:len(rating_counts)]
    rating_counts.plot(kind='bar', ax=ax2, color=colors, edgecolor='white')
    ax2.set_title('Stocks by Valuation Category', fontweight='bold')
    ax2.set_xlabel('')
    ax2.set_ylabel('Number of Stocks')
    ax2.tick_params(axis='x', rotation=45)

    # 3. Valuation by sector
    ax3 = axes[1, 0]
    sector_val = df.groupby('sector')['valuation_score'].agg(['mean', 'std']).sort_values('mean')
    sector_val['mean'].plot(kind='barh', ax=ax3, xerr=sector_val['std'],
                            color='steelblue', capsize=3)
    ax3.set_title('Mean Valuation Score by Sector', fontweight='bold')
    ax3.set_xlabel('Valuation Score')

    # 4. Forward P/E vs Valuation Score scatter
    ax4 = axes[1, 1]
    valid = df[['forward_pe', 'valuation_score']].dropna()
    valid = valid[valid['forward_pe'] > 0]
    valid = valid[valid['forward_pe'] < valid['forward_pe'].quantile(0.95)]  # Remove outliers
    ax4.scatter(valid['forward_pe'], valid['valuation_score'], alpha=0.5, s=20)
    ax4.set_title('Forward P/E vs Valuation Score', fontweight='bold')
    ax4.set_xlabel('Forward P/E')
    ax4.set_ylabel('Valuation Score')

    # Add regression line
    if len(valid) > 10:
        z = np.polyfit(valid['forward_pe'], valid['valuation_score'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(valid['forward_pe'].min(), valid['forward_pe'].max(), 100)
        ax4.plot(x_line, p(x_line), 'r--', alpha=0.7, label=f'Trend')
        ax4.legend()

    plt.suptitle('Valuation Analysis Dashboard', fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


# =============================================================================
# PEER GROUP & OUTLIER ANALYSIS
# =============================================================================

def plot_sector_boxplots(df, metrics, title="Metric Distributions by Sector", save_path=None):
    """Create box plots for outlier detection in peer groups"""
    setup_plot_style()

    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(5 * n_metrics, 8))

    if n_metrics == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        df_plot = df[[metric, 'sector']].dropna()

        # Remove extreme outliers for visualization
        q_low = df_plot[metric].quantile(0.02)
        q_high = df_plot[metric].quantile(0.98)
        df_plot = df_plot[(df_plot[metric] >= q_low) & (df_plot[metric] <= q_high)]

        order = df_plot.groupby('sector')[metric].median().sort_values().index
        sns.boxplot(data=df_plot, x='sector', y=metric, order=order, ax=ax, palette='Set2')
        ax.set_title(metric.replace('_', ' ').title(), fontweight='bold')
        ax.tick_params(axis='x', rotation=90)
        ax.set_xlabel('')

    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_waterfall_decomposition(contributions, title="Return Decomposition", save_path=None):
    """
    Create waterfall chart for return/profit decomposition
    contributions: dict with {factor_name: contribution_value}
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=(12, 6))

    factors = list(contributions.keys())
    values = list(contributions.values())

    # Calculate positions
    cumsum = np.cumsum([0] + values[:-1])

    colors = ['green' if v > 0 else 'red' for v in values]

    ax.bar(factors, values, bottom=cumsum, color=colors, edgecolor='white', width=0.7)

    # Add value labels
    for i, (factor, value, cs) in enumerate(zip(factors, values, cumsum)):
        if value >= 0:
            ax.text(i, cs + value + 0.5, f'+{value:.1f}%', ha='center', fontsize=9)
        else:
            ax.text(i, cs + value - 1.5, f'{value:.1f}%', ha='center', fontsize=9)

    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_title(title, fontweight='bold', fontsize=14)
    ax.set_ylabel('Contribution (%)')
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


# =============================================================================
# MULTI-AXIS TECHNICAL CHARTS
# =============================================================================

def plot_price_volume_rsi(prices, volume, rsi, ticker="Stock", save_path=None):
    """Create multi-axis chart with price, volume, and RSI"""
    setup_plot_style()

    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1], hspace=0.1)

    # Price chart
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(prices.index, prices, 'b-', linewidth=1.5, label='Price')
    ax1.fill_between(prices.index, prices, alpha=0.2)
    ax1.set_title(f'{ticker} - Price, Volume & RSI Analysis', fontweight='bold', fontsize=14)
    ax1.set_ylabel('Price ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticklabels([])

    # Volume chart
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    colors = ['green' if prices.iloc[i] >= prices.iloc[i-1] else 'red'
              for i in range(1, len(prices))]
    colors = ['gray'] + colors
    ax2.bar(volume.index, volume, color=colors, alpha=0.7, width=1)
    ax2.set_ylabel('Volume')
    ax2.set_xticklabels([])

    # RSI chart
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.plot(rsi.index, rsi, 'purple', linewidth=1.5, label='RSI')
    ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought')
    ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold')
    ax3.fill_between(rsi.index, 30, 70, alpha=0.1, color='gray')
    ax3.set_ylabel('RSI')
    ax3.set_ylim(0, 100)
    ax3.legend(loc='upper left', fontsize=8)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


# =============================================================================
# COMPREHENSIVE DASHBOARD
# =============================================================================

def create_stock_dashboard(stock_data, technicals, save_path=None):
    """Create comprehensive dashboard for a single stock"""
    setup_plot_style()

    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

    ticker = stock_data.get('ticker', 'Stock')

    # 1. Key metrics summary (text)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    metrics_text = f"""
    {ticker} Summary
    {'='*30}
    Price: ${stock_data.get('current_price', 0):,.2f}
    Market Cap: ${stock_data.get('market_cap', 0)/1e9:,.1f}B
    Sector: {stock_data.get('sector', 'N/A')}

    Valuation:
    Forward P/E: {stock_data.get('forward_pe', 0):.1f}
    P/B: {stock_data.get('price_to_book', 0):.1f}
    EV/EBITDA: {stock_data.get('ev_to_ebitda', 0):.1f}

    Profitability:
    ROE: {stock_data.get('roe', 0)*100:.1f}%
    Profit Margin: {stock_data.get('profit_margin', 0)*100:.1f}%

    Financial Health:
    D/E: {stock_data.get('debt_to_equity', 0):.0f}
    Current Ratio: {stock_data.get('current_ratio', 0):.1f}

    Rating: {stock_data.get('valuation_category', 'N/A')}
    """
    ax1.text(0.1, 0.9, metrics_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 2. Technical indicators gauge
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    tech_text = f"""
    Technical Indicators
    {'='*30}
    RSI: {technicals.get('rsi', 0):.1f}
    {'[OVERSOLD]' if technicals.get('rsi_oversold') else '[OVERBOUGHT]' if technicals.get('rsi_overbought') else ''}

    MACD: {technicals.get('macd', 0):.2f}
    Signal: {technicals.get('macd_signal', 0):.2f}
    {'[BULLISH]' if technicals.get('macd_bullish') else '[BEARISH]'}

    BB %B: {technicals.get('bb_percent_b', 0):.2f}

    Price vs SMA200: {technicals.get('price_vs_sma_200', 0)*100:+.1f}%

    ADX: {technicals.get('adx', 0):.1f}
    {'[STRONG TREND]' if technicals.get('strong_trend') else '[WEAK TREND]'}

    Volume Ratio: {technicals.get('volume_ratio', 0):.2f}x
    """
    ax2.text(0.1, 0.9, tech_text, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    # 3. Peer comparison placeholder
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    ax3.text(0.5, 0.5, 'Peer Comparison\n(See Sector Analysis)',
             transform=ax3.transAxes, fontsize=12, ha='center', va='center')

    # 4-6. More visualizations can be added

    plt.suptitle(f'{ticker} Comprehensive Analysis Dashboard', fontsize=16, fontweight='bold')

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def create_all_plots(df, sector_metrics, output_dir='.'):
    """Generate all analysis plots and save to directory"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("\nGenerating visualizations...")

    # 1. Sector comparison dashboard
    print("  - Sector comparison dashboard...")
    plot_sector_comparison(df, save_path=f'{output_dir}/sector_comparison.png')

    # 2. Sector heatmap
    print("  - Sector heatmap...")
    metrics = ['forward_pe', 'price_to_book', 'debt_to_equity', 'roe', 'profit_margin', 'revenue_growth']
    metrics = [m for m in metrics if m in df.columns]
    plot_sector_heatmap(df, metrics, save_path=f'{output_dir}/sector_heatmap.png')

    # 3. Correlation matrix
    print("  - Correlation matrix...")
    corr_metrics = ['forward_pe', 'price_to_book', 'debt_to_equity', 'roe',
                    'revenue_growth', '1y_return', 'volatility', 'excess_return']
    corr_metrics = [m for m in corr_metrics if m in df.columns]
    plot_correlation_matrix(df, corr_metrics, save_path=f'{output_dir}/correlation_matrix.png')

    # 4. Sector correlations
    print("  - Sector excess return correlations...")
    plot_sector_correlations(df, save_path=f'{output_dir}/sector_correlations.png')

    # 5. Risk-return scatter
    print("  - Risk-return analysis...")
    plot_risk_return_scatter(df, save_path=f'{output_dir}/risk_return_scatter.png')

    # 6. Valuation distribution
    print("  - Valuation distribution...")
    plot_valuation_distribution(df, save_path=f'{output_dir}/valuation_distribution.png')

    # 7. Box plots for outlier detection
    print("  - Sector box plots...")
    box_metrics = ['forward_pe', 'debt_to_equity', 'roe', 'profit_margin']
    box_metrics = [m for m in box_metrics if m in df.columns]
    plot_sector_boxplots(df, box_metrics, save_path=f'{output_dir}/sector_boxplots.png')

    print(f"  All plots saved to {output_dir}/")
