# Sector Analysis System

A comprehensive stock analysis system that fetches fundamental data from S&P 500 and NASDAQ stocks, analyzes them by sector, and rates them from undervalued to overvalued.

## Features

### Data Collection
- Fetches stock data from Yahoo Finance API
- S&P 500 and NASDAQ 100 stock coverage
- Fallback ticker list when web scraping is unavailable

### Fundamental Analysis
- **Valuation Metrics**: Forward P/E, Trailing P/E, PEG Ratio, Price-to-Book, EV/EBITDA
- **Profitability**: ROE, ROA, Profit Margin, Operating Margin, Gross Margin
- **Financial Health**: Debt-to-Equity, Current Ratio, Quick Ratio
- **Growth**: Revenue Growth, Earnings Growth
- **Cash Flow**: Free Cash Flow, Operating Cash Flow

### Technical Analysis
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Moving Averages (SMA/EMA 20, 50, 100, 200)
- Stochastic Oscillator
- ADX (Average Directional Index)
- Volume Analysis

### Composite Scores
- Altman Z-Score (bankruptcy prediction)
- Piotroski F-Score (financial health)
- Composite Quality Score

### Valuation Rating System
Stocks are rated in 5 categories:
1. **Strongly Undervalued** - Best value opportunities
2. **Undervalued** - Good value
3. **Fairly Valued** - At fair market price
4. **Overvalued** - Trading above fair value
5. **Strongly Overvalued** - Most expensive relative to fundamentals

### Regression Analysis
- OLS Regression for factor analysis
- Sector-specific regression models
- Machine Learning models:
  - Ridge Regression
  - Lasso Regression
  - ElasticNet
  - Random Forest
  - Gradient Boosting

### Visualizations
- Sector comparison dashboards
- Correlation matrices
- Risk-return scatter plots
- Valuation distribution histograms
- Sector box plots for outlier detection
- Heatmaps for sector metrics

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run with real data (requires internet)
```bash
cd src
python main.py --output ../output
```

### Run with demo data (no internet required)
```bash
cd src
python main.py --demo --output ../output
```

### Command Line Options
```
--sample, -s    Sample size (number of stocks)
--output, -o    Output directory (default: output)
--skip-plots    Skip plot generation
--demo, -d      Use demo data (simulated data)
```

## Output Files

| File | Description |
|------|-------------|
| `stock_ratings.csv` | Complete stock ratings with all metrics |
| `sector_summary.csv` | Sector-level summary statistics |
| `top_picks_by_sector.csv` | Top undervalued picks by sector |
| `regression_report.txt` | Detailed regression analysis report |
| `sector_comparison.png` | Sector comparison dashboard |
| `sector_heatmap.png` | Sector metrics heatmap |
| `correlation_matrix.png` | Correlation matrix of key metrics |
| `sector_correlations.png` | Excess returns vs fundamentals |
| `risk_return_scatter.png` | Risk-return analysis by sector |
| `valuation_distribution.png` | Valuation score distributions |
| `sector_boxplots.png` | Box plots for outlier detection |

## Project Structure

```
Sector-Analysis/
├── src/
│   ├── main.py                 # Main runner script
│   ├── data_fetcher.py         # Data collection module
│   ├── fundamental_analysis.py # Fundamental analysis engine
│   ├── advanced_metrics.py     # Performance & composite scores
│   ├── technical_analysis.py   # Technical indicators
│   ├── visualization.py        # Plotting functions
│   ├── regression_models.py    # OLS & ML models
│   └── demo_data.py           # Demo data generator
├── output/                     # Generated reports and plots
├── requirements.txt
└── README.md
```

## Metrics Covered

### Price & Performance
- Cumulative Return, Annualized Return
- Maximum Drawdown, Recovery Time
- Volatility, Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Alpha, Beta, Tracking Error, Information Ratio
- Up/Down Capture Ratios

### Fundamental Valuation
- P/E Ratios (Trailing, Forward)
- P/B Ratio, P/S Ratio
- EV/EBITDA, EV/Revenue
- FCF Yield, Dividend Yield

### Balance Sheet
- Current Ratio, Quick Ratio, Cash Ratio
- Debt/Equity, Debt/EBITDA
- Interest Coverage Ratio

### Sector-Relative
- Valuation percentiles within sector
- Growth vs sector average
- Margin comparison
- Beta to sector

## Sectors Covered

1. Technology
2. Health Care
3. Financials
4. Consumer Discretionary
5. Consumer Staples
6. Industrials
7. Energy
8. Communication Services
9. Materials
10. Real Estate
11. Utilities

## License

MIT License
