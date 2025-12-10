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


# =============================================================================
# ADVANCED VISUALIZATION FUNCTIONS
# =============================================================================

def plot_quality_scores_dashboard(df, save_path=None):
    """
    Create dashboard showing quality scores (Z-Score, F-Score, Quality Score)
    """
    setup_plot_style()

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. Altman Z-Score Distribution
    if 'altman_z_score' in df.columns:
        ax1 = axes[0, 0]
        z_scores = df['altman_z_score'].dropna()
        z_scores = z_scores[(z_scores > -5) & (z_scores < 10)]  # Remove outliers

        colors = []
        for z in z_scores:
            if z > 2.99:
                colors.append('green')
            elif z > 1.81:
                colors.append('yellow')
            else:
                colors.append('red')

        ax1.hist(z_scores, bins=30, color='steelblue', edgecolor='white', alpha=0.7)
        ax1.axvline(x=2.99, color='green', linestyle='--', label='Safe Zone (>2.99)')
        ax1.axvline(x=1.81, color='orange', linestyle='--', label='Grey Zone (1.81-2.99)')
        ax1.set_title('Altman Z-Score Distribution', fontweight='bold')
        ax1.set_xlabel('Z-Score')
        ax1.legend(fontsize=8)

    # 2. Piotroski F-Score Distribution
    if 'piotroski_f_score' in df.columns:
        ax2 = axes[0, 1]
        f_scores = df['piotroski_f_score'].dropna()
        score_counts = f_scores.value_counts().sort_index()
        colors = ['red' if x < 4 else ('yellow' if x < 7 else 'green') for x in score_counts.index]
        ax2.bar(score_counts.index, score_counts.values, color=colors, edgecolor='white')
        ax2.set_title('Piotroski F-Score Distribution', fontweight='bold')
        ax2.set_xlabel('F-Score (0-9)')
        ax2.set_ylabel('Number of Stocks')

    # 3. Quality Score Distribution
    if 'quality_score' in df.columns:
        ax3 = axes[0, 2]
        q_scores = df['quality_score'].dropna()
        ax3.hist(q_scores, bins=20, color='steelblue', edgecolor='white', alpha=0.7)
        ax3.axvline(x=q_scores.median(), color='red', linestyle='--', label=f'Median: {q_scores.median():.0f}')
        ax3.set_title('Quality Score Distribution', fontweight='bold')
        ax3.set_xlabel('Quality Score (0-100)')
        ax3.legend()

    # 4. Z-Score by Sector
    if 'altman_z_score' in df.columns:
        ax4 = axes[1, 0]
        sector_z = df.groupby('sector')['altman_z_score'].median().sort_values()
        colors = ['green' if z > 2.99 else ('yellow' if z > 1.81 else 'red') for z in sector_z]
        sector_z.plot(kind='barh', ax=ax4, color=colors)
        ax4.axvline(x=2.99, color='green', linestyle='--', alpha=0.5)
        ax4.axvline(x=1.81, color='orange', linestyle='--', alpha=0.5)
        ax4.set_title('Median Z-Score by Sector', fontweight='bold')

    # 5. F-Score by Sector
    if 'piotroski_f_score' in df.columns:
        ax5 = axes[1, 1]
        sector_f = df.groupby('sector')['piotroski_f_score'].median().sort_values()
        colors = ['red' if f < 4 else ('yellow' if f < 7 else 'green') for f in sector_f]
        sector_f.plot(kind='barh', ax=ax5, color=colors)
        ax5.set_title('Median F-Score by Sector', fontweight='bold')

    # 6. Quality vs Valuation Scatter
    if 'quality_score' in df.columns and 'forward_pe' in df.columns:
        ax6 = axes[1, 2]
        valid = df[['quality_score', 'forward_pe', 'sector']].dropna()
        valid = valid[valid['forward_pe'] < valid['forward_pe'].quantile(0.95)]

        for sector in valid['sector'].unique():
            sector_data = valid[valid['sector'] == sector]
            ax6.scatter(sector_data['forward_pe'], sector_data['quality_score'],
                       alpha=0.6, s=30, label=sector)
        ax6.set_xlabel('Forward P/E')
        ax6.set_ylabel('Quality Score')
        ax6.set_title('Quality Score vs Valuation', fontweight='bold')
        ax6.legend(fontsize=7, loc='best', ncol=2)

    plt.suptitle('Composite Quality Scores Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_performance_metrics_dashboard(df, save_path=None):
    """
    Create dashboard showing performance metrics (Sharpe, Sortino, Drawdown)
    """
    setup_plot_style()

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. Sharpe Ratio Distribution
    if 'sharpe_ratio' in df.columns or 'sharpe_approx' in df.columns:
        ax1 = axes[0, 0]
        sharpe_col = 'sharpe_ratio' if 'sharpe_ratio' in df.columns else 'sharpe_approx'
        sharpe = df[sharpe_col].dropna()
        sharpe = sharpe[(sharpe > -3) & (sharpe < 5)]  # Remove outliers
        ax1.hist(sharpe, bins=30, color='steelblue', edgecolor='white', alpha=0.7)
        ax1.axvline(x=0, color='red', linestyle='--', label='Break-even')
        ax1.axvline(x=1, color='green', linestyle='--', label='Good (>1)')
        ax1.set_title('Sharpe Ratio Distribution', fontweight='bold')
        ax1.set_xlabel('Sharpe Ratio')
        ax1.legend()

    # 2. Max Drawdown Distribution
    if 'max_drawdown' in df.columns:
        ax2 = axes[0, 1]
        dd = df['max_drawdown'].dropna() * 100
        dd = dd[dd > -80]  # Remove extreme outliers
        ax2.hist(dd, bins=30, color='red', edgecolor='white', alpha=0.7)
        ax2.axvline(x=dd.median(), color='black', linestyle='--', label=f'Median: {dd.median():.1f}%')
        ax2.set_title('Max Drawdown Distribution', fontweight='bold')
        ax2.set_xlabel('Max Drawdown (%)')
        ax2.legend()

    # 3. Volatility Distribution
    if 'volatility' in df.columns:
        ax3 = axes[0, 2]
        vol = df['volatility'].dropna() * 100
        vol = vol[vol < vol.quantile(0.98)]
        ax3.hist(vol, bins=30, color='orange', edgecolor='white', alpha=0.7)
        ax3.axvline(x=vol.median(), color='black', linestyle='--', label=f'Median: {vol.median():.1f}%')
        ax3.set_title('Annualized Volatility Distribution', fontweight='bold')
        ax3.set_xlabel('Volatility (%)')
        ax3.legend()

    # 4. Sharpe by Sector
    if 'sharpe_ratio' in df.columns or 'sharpe_approx' in df.columns:
        ax4 = axes[1, 0]
        sharpe_col = 'sharpe_ratio' if 'sharpe_ratio' in df.columns else 'sharpe_approx'
        sector_sharpe = df.groupby('sector')[sharpe_col].median().sort_values()
        colors = ['green' if s > 0.5 else ('yellow' if s > 0 else 'red') for s in sector_sharpe]
        sector_sharpe.plot(kind='barh', ax=ax4, color=colors)
        ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_title('Median Sharpe Ratio by Sector', fontweight='bold')

    # 5. Max Drawdown by Sector
    if 'max_drawdown' in df.columns:
        ax5 = axes[1, 1]
        sector_dd = df.groupby('sector')['max_drawdown'].median().sort_values(ascending=False) * 100
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(sector_dd)))
        sector_dd.plot(kind='barh', ax=ax5, color=colors)
        ax5.set_title('Median Max Drawdown by Sector', fontweight='bold')
        ax5.set_xlabel('Max Drawdown (%)')

    # 6. Risk-Return Efficient Frontier
    ax6 = axes[1, 2]
    if 'volatility' in df.columns and '1y_return' in df.columns:
        valid = df[['volatility', '1y_return', 'sector']].dropna()
        valid = valid[(valid['volatility'] < valid['volatility'].quantile(0.95)) &
                      (valid['1y_return'].abs() < 2)]

        for sector in valid['sector'].unique():
            sector_data = valid[valid['sector'] == sector]
            ax6.scatter(sector_data['volatility'] * 100, sector_data['1y_return'] * 100,
                       alpha=0.5, s=20, label=sector)

        ax6.set_xlabel('Volatility (%)')
        ax6.set_ylabel('1Y Return (%)')
        ax6.set_title('Risk-Return by Stock', fontweight='bold')
        ax6.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax6.legend(fontsize=6, loc='best', ncol=2)

    plt.suptitle('Performance Metrics Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_technical_overview(df, save_path=None):
    """
    Create dashboard showing technical indicators summary
    """
    setup_plot_style()

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. RSI Distribution
    if 'rsi' in df.columns:
        ax1 = axes[0, 0]
        rsi = df['rsi'].dropna()
        colors = ['green' if r < 30 else ('red' if r > 70 else 'gray') for r in rsi]
        ax1.hist(rsi, bins=30, color='steelblue', edgecolor='white', alpha=0.7)
        ax1.axvline(x=30, color='green', linestyle='--', label='Oversold (<30)')
        ax1.axvline(x=70, color='red', linestyle='--', label='Overbought (>70)')
        ax1.axvspan(30, 70, alpha=0.1, color='gray')
        ax1.set_title('RSI Distribution', fontweight='bold')
        ax1.set_xlabel('RSI')
        ax1.legend()

    # 2. RSI by Sector
    if 'rsi' in df.columns:
        ax2 = axes[0, 1]
        sector_rsi = df.groupby('sector')['rsi'].median().sort_values()
        colors = ['green' if r < 40 else ('red' if r > 60 else 'gray') for r in sector_rsi]
        sector_rsi.plot(kind='barh', ax=ax2, color=colors)
        ax2.axvline(x=50, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('Median RSI by Sector', fontweight='bold')

    # 3. Price vs 200 SMA
    if 'price_vs_sma_200' in df.columns:
        ax3 = axes[0, 2]
        pct_above = (df['price_vs_sma_200'] > 0).mean() * 100
        pct_below = 100 - pct_above
        ax3.pie([pct_above, pct_below],
                labels=[f'Above 200 SMA\n({pct_above:.1f}%)', f'Below 200 SMA\n({pct_below:.1f}%)'],
                colors=['green', 'red'], autopct='', startangle=90)
        ax3.set_title('Stocks vs 200-Day SMA', fontweight='bold')

    # 4. Technical Signal Distribution
    if 'technical_signal' in df.columns:
        ax4 = axes[1, 0]
        signal_counts = df['technical_signal'].value_counts()
        order = ['Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell']
        signal_counts = signal_counts.reindex([s for s in order if s in signal_counts.index])
        colors = ['darkgreen', 'lightgreen', 'gray', 'orange', 'red'][:len(signal_counts)]
        signal_counts.plot(kind='bar', ax=ax4, color=colors, edgecolor='white')
        ax4.set_title('Technical Signal Distribution', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)

    # 5. Volume Ratio Distribution
    if 'volume_ratio' in df.columns:
        ax5 = axes[1, 1]
        vol_ratio = df['volume_ratio'].dropna()
        vol_ratio = vol_ratio[vol_ratio < vol_ratio.quantile(0.98)]
        ax5.hist(vol_ratio, bins=30, color='steelblue', edgecolor='white', alpha=0.7)
        ax5.axvline(x=1, color='black', linestyle='--', label='Average Volume')
        ax5.axvline(x=1.5, color='orange', linestyle='--', label='High Volume (1.5x)')
        ax5.set_title('Volume Ratio Distribution', fontweight='bold')
        ax5.set_xlabel('Volume vs 20-Day Avg')
        ax5.legend()

    # 6. ADX Trend Strength
    if 'adx' in df.columns:
        ax6 = axes[1, 2]
        adx = df['adx'].dropna()
        adx = adx[adx < 100]
        ax6.hist(adx, bins=30, color='purple', edgecolor='white', alpha=0.7)
        ax6.axvline(x=25, color='orange', linestyle='--', label='Strong Trend (>25)')
        ax6.axvline(x=50, color='red', linestyle='--', label='Very Strong (>50)')
        ax6.set_title('ADX Distribution (Trend Strength)', fontweight='bold')
        ax6.set_xlabel('ADX')
        ax6.legend()

    plt.suptitle('Technical Indicators Overview', fontsize=16, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_multi_factor_radar(df, ticker, metrics, save_path=None):
    """
    Create radar/spider chart for multi-factor comparison
    """
    setup_plot_style()

    # Get stock data
    stock = df[df['ticker'] == ticker]
    if len(stock) == 0:
        return None

    stock = stock.iloc[0]

    # Get sector for comparison
    sector = stock['sector']
    sector_median = df[df['sector'] == sector][metrics].median()

    # Normalize values to 0-100 percentile within dataset
    percentiles = {}
    for metric in metrics:
        if pd.notna(stock.get(metric)):
            percentiles[metric] = (df[metric] < stock[metric]).mean() * 100
        else:
            percentiles[metric] = 50

    # Create radar chart
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    values = [percentiles[m] for m in metrics]
    values += values[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    ax.plot(angles, values, 'o-', linewidth=2, color='blue', label=ticker)
    ax.fill(angles, values, alpha=0.25, color='blue')

    # Add 50th percentile reference
    ref_values = [50] * len(metrics) + [50]
    ax.plot(angles, ref_values, '--', linewidth=1, color='gray', label='Market Median')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.replace('_', '\n').title() for m in metrics], size=9)
    ax.set_ylim(0, 100)
    ax.set_title(f'{ticker} Multi-Factor Analysis\n(Percentile Rank)', fontweight='bold', size=14)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def plot_sector_performance_heatmap(df, save_path=None):
    """
    Create heatmap showing sector performance across multiple timeframes
    """
    setup_plot_style()

    return_cols = ['1w_return', '1m_return', '3m_return', '6m_return', '1y_return']
    available_cols = [c for c in return_cols if c in df.columns]

    if len(available_cols) == 0:
        return None

    # Calculate sector medians
    sector_returns = df.groupby('sector')[available_cols].median() * 100

    # Rename columns for display
    col_names = {
        '1w_return': '1 Week',
        '1m_return': '1 Month',
        '3m_return': '3 Months',
        '6m_return': '6 Months',
        '1y_return': '1 Year'
    }
    sector_returns.columns = [col_names.get(c, c) for c in sector_returns.columns]

    fig, ax = plt.subplots(figsize=(12, 8))

    sns.heatmap(sector_returns, annot=True, fmt='.1f', cmap='RdYlGn',
                center=0, linewidths=0.5, ax=ax,
                cbar_kws={'label': 'Return (%)'})

    ax.set_title('Sector Performance Heatmap', fontsize=14, fontweight='bold')
    ax.set_xlabel('Time Period')
    ax.set_ylabel('Sector')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
    return fig


def create_comprehensive_plots(df, sector_metrics, output_dir='.'):
    """Generate all comprehensive analysis plots"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("\nGenerating comprehensive visualizations...")

    # Original plots
    create_all_plots(df, sector_metrics, output_dir)

    # Additional comprehensive plots
    print("  - Quality scores dashboard...")
    try:
        plot_quality_scores_dashboard(df, save_path=f'{output_dir}/quality_scores_dashboard.png')
    except Exception as e:
        print(f"    Warning: Could not create quality scores dashboard: {e}")

    print("  - Performance metrics dashboard...")
    try:
        plot_performance_metrics_dashboard(df, save_path=f'{output_dir}/performance_dashboard.png')
    except Exception as e:
        print(f"    Warning: Could not create performance dashboard: {e}")

    print("  - Technical overview...")
    try:
        plot_technical_overview(df, save_path=f'{output_dir}/technical_overview.png')
    except Exception as e:
        print(f"    Warning: Could not create technical overview: {e}")

    print("  - Sector performance heatmap...")
    try:
        plot_sector_performance_heatmap(df, save_path=f'{output_dir}/sector_performance_heatmap.png')
    except Exception as e:
        print(f"    Warning: Could not create sector performance heatmap: {e}")

    print(f"\n  All comprehensive plots saved to {output_dir}/")
