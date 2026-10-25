"""
Technical Analysis Module
=========================
Comprehensive technical indicators and market sentiment metrics including:

1. PRICE-BASED INDICATORS
   - RSI, MACD, Bollinger Bands, Moving Averages
   - Stochastic Oscillator, Williams %R, CCI
   - Support/Resistance, ATR, Parabolic SAR

2. VOLUME-BASED INDICATORS
   - OBV, VWAP, MFI, Accumulation/Distribution
   - Volume Ratio, Bid-Ask Spread Analysis

3. MOMENTUM INDICATORS
   - Momentum, ROC, TRIX

4. TREND INDICATORS
   - ADX, Parabolic SAR, Ichimoku Cloud

5. MARKET SENTIMENT
   - Put/Call Ratio, Short Interest Analysis
   - Insider Trading Activity Indicators

6. TIME-BASED ANALYSIS
   - Seasonality Patterns
   - Earnings Surprise History
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# 1. PRICE-BASED TECHNICAL INDICATORS
# =============================================================================

def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI)
    RSI > 70: Overbought
    RSI < 30: Oversold
    RSI 50: Neutral momentum
    """
    if prices is None or len(prices) < period + 1:
        return pd.Series(index=prices.index if prices is not None else [], dtype=float)

    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Use exponential moving average for smoothing
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)

    Components:
    - MACD Line: Fast EMA - Slow EMA
    - Signal Line: EMA of MACD Line
    - Histogram: MACD Line - Signal Line

    Signals:
    - MACD crosses above Signal: Bullish
    - MACD crosses below Signal: Bearish
    - Histogram positive/negative: Momentum direction
    """
    if prices is None or len(prices) < slow + signal:
        empty = pd.Series(index=prices.index if prices is not None else [], dtype=float)
        return empty, empty, empty

    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """
    Calculate Bollinger Bands

    Returns:
    - Upper Band: SMA + (std_dev * Standard Deviation)
    - Middle Band: SMA
    - Lower Band: SMA - (std_dev * Standard Deviation)
    - %B: Position within bands (0 = lower, 1 = upper)
    - Bandwidth: Width of bands (volatility measure)
    """
    if prices is None or len(prices) < period:
        empty = pd.Series(index=prices.index if prices is not None else [], dtype=float)
        return empty, empty, empty, empty, empty

    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    # %B indicates where price is relative to bands
    percent_b = (prices - lower) / (upper - lower)

    # Bandwidth indicates volatility (higher = more volatile)
    bandwidth = (upper - lower) / middle

    return upper, middle, lower, percent_b, bandwidth


def calculate_moving_averages(prices, periods=[10, 20, 50, 100, 200]):
    """
    Calculate Simple and Exponential Moving Averages

    Common interpretations:
    - Price > MA: Bullish trend
    - Price < MA: Bearish trend
    - Golden Cross (50 > 200): Major bullish signal
    - Death Cross (50 < 200): Major bearish signal
    """
    mas = {}

    if prices is None:
        return mas

    for period in periods:
        if len(prices) >= period:
            mas[f'sma_{period}'] = prices.rolling(window=period).mean()
            mas[f'ema_{period}'] = prices.ewm(span=period, adjust=False).mean()
        else:
            mas[f'sma_{period}'] = pd.Series(index=prices.index, dtype=float)
            mas[f'ema_{period}'] = pd.Series(index=prices.index, dtype=float)

    return mas


def calculate_support_resistance(prices, window=20, n_levels=3):
    """
    Calculate Support and Resistance levels using pivot points

    Returns dict with:
    - support_levels: List of support prices
    - resistance_levels: List of resistance prices
    - nearest_support: Closest support below current price
    - nearest_resistance: Closest resistance above current price
    """
    if prices is None or len(prices) < window * 2:
        return {'support': np.nan, 'resistance': np.nan}

    # Find local minima and maxima
    rolling_max = prices.rolling(window=window, center=True).max()
    rolling_min = prices.rolling(window=window, center=True).min()

    # Identify pivot points
    peaks = prices[prices == rolling_max].dropna()
    troughs = prices[prices == rolling_min].dropna()

    current_price = prices.iloc[-1]

    # Get unique levels
    resistance_levels = sorted(peaks.unique()[peaks.unique() > current_price])[:n_levels]
    support_levels = sorted(troughs.unique()[troughs.unique() < current_price], reverse=True)[:n_levels]

    result = {
        'support_levels': support_levels,
        'resistance_levels': resistance_levels,
        'nearest_support': support_levels[0] if len(support_levels) > 0 else np.nan,
        'nearest_resistance': resistance_levels[0] if len(resistance_levels) > 0 else np.nan,
    }

    return result


def calculate_atr(high, low, close, period=14):
    """
    Calculate Average True Range (ATR)
    Measures volatility - useful for stop-loss placement
    """
    if any(x is None or len(x) < period + 1 for x in [high, low, close]):
        return pd.Series(dtype=float)

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def calculate_stochastic(high, low, close, k_period=14, d_period=3):
    """
    Calculate Stochastic Oscillator (%K and %D)

    %K > 80: Overbought
    %K < 20: Oversold

    %K crossing above %D: Bullish
    %K crossing below %D: Bearish
    """
    if any(x is None or len(x) < k_period for x in [high, low, close]):
        empty = pd.Series(dtype=float)
        return empty, empty

    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()

    return k, d


def calculate_williams_r(high, low, close, period=14):
    """
    Calculate Williams %R

    > -20: Overbought
    < -80: Oversold
    """
    if any(x is None or len(x) < period for x in [high, low, close]):
        return pd.Series(dtype=float)

    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()

    williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)

    return williams_r


def calculate_cci(high, low, close, period=20):
    """
    Calculate Commodity Channel Index

    > 100: Overbought / Strong uptrend
    < -100: Oversold / Strong downtrend
    """
    if any(x is None or len(x) < period for x in [high, low, close]):
        return pd.Series(dtype=float)

    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean()
    )

    cci = (typical_price - sma_tp) / (0.015 * mean_deviation)

    return cci


def calculate_pivot_points(high, low, close):
    """
    Calculate Classic Pivot Points

    Returns pivot point and support/resistance levels
    """
    if any(x is None for x in [high, low, close]):
        return {}

    # Use previous day's data
    h = high.iloc[-2] if len(high) > 1 else high.iloc[-1]
    l = low.iloc[-2] if len(low) > 1 else low.iloc[-1]
    c = close.iloc[-2] if len(close) > 1 else close.iloc[-1]

    pivot = (h + l + c) / 3
    r1 = 2 * pivot - l
    s1 = 2 * pivot - h
    r2 = pivot + (h - l)
    s2 = pivot - (h - l)
    r3 = h + 2 * (pivot - l)
    s3 = l - 2 * (h - pivot)

    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2, 'r3': r3,
        's1': s1, 's2': s2, 's3': s3
    }


# =============================================================================
# 2. VOLUME-BASED INDICATORS
# =============================================================================

def calculate_obv(close, volume):
    """
    Calculate On-Balance Volume (OBV)

    OBV rising with price: Confirms uptrend
    OBV falling with price: Confirms downtrend
    Divergence: Potential reversal signal
    """
    if close is None or volume is None:
        return pd.Series(dtype=float)

    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_vwap(high, low, close, volume):
    """
    Calculate Volume-Weighted Average Price (VWAP)

    Price above VWAP: Bullish bias
    Price below VWAP: Bearish bias
    """
    if any(x is None for x in [high, low, close, volume]):
        return pd.Series(dtype=float)

    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap


def calculate_volume_ratio(volume, period=20):
    """
    Calculate current volume vs average volume

    > 1.5: High volume (significant move)
    < 0.5: Low volume (lack of conviction)
    """
    if volume is None or len(volume) < period:
        return pd.Series(dtype=float)

    avg_volume = volume.rolling(window=period).mean()
    return volume / avg_volume


def calculate_mfi(high, low, close, volume, period=14):
    """
    Calculate Money Flow Index (Volume-weighted RSI)

    > 80: Overbought
    < 20: Oversold
    """
    if any(x is None or len(x) < period + 1 for x in [high, low, close, volume]):
        return pd.Series(dtype=float)

    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume

    positive_flow = pd.Series(0.0, index=close.index)
    negative_flow = pd.Series(0.0, index=close.index)

    tp_diff = typical_price.diff()
    positive_flow[tp_diff > 0] = raw_money_flow[tp_diff > 0]
    negative_flow[tp_diff < 0] = raw_money_flow[tp_diff < 0]

    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()

    money_ratio = positive_mf / negative_mf
    mfi = 100 - (100 / (1 + money_ratio))

    return mfi


def calculate_accumulation_distribution(high, low, close, volume):
    """
    Calculate Accumulation/Distribution Line

    Measures buying/selling pressure
    Rising AD with rising price: Accumulation (bullish)
    Falling AD with falling price: Distribution (bearish)
    """
    if any(x is None for x in [high, low, close, volume]):
        return pd.Series(dtype=float)

    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)
    ad = (clv * volume).cumsum()
    return ad


def calculate_chaikin_money_flow(high, low, close, volume, period=20):
    """
    Calculate Chaikin Money Flow

    > 0: Buying pressure
    < 0: Selling pressure
    """
    if any(x is None or len(x) < period for x in [high, low, close, volume]):
        return pd.Series(dtype=float)

    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)

    cmf = (clv * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
    return cmf


# =============================================================================
# 3. MOMENTUM INDICATORS
# =============================================================================

def calculate_momentum(prices, period=10):
    """Calculate price momentum (simple difference)"""
    if prices is None or len(prices) < period:
        return pd.Series(dtype=float)
    return prices - prices.shift(period)


def calculate_roc(prices, period=10):
    """
    Calculate Rate of Change (ROC)

    ROC = ((Price - Price_n) / Price_n) * 100
    """
    if prices is None or len(prices) < period:
        return pd.Series(dtype=float)
    return ((prices / prices.shift(period)) - 1) * 100


def calculate_trix(prices, period=15):
    """
    Calculate TRIX (Triple Exponential Moving Average)

    Crossing above zero: Bullish
    Crossing below zero: Bearish
    """
    if prices is None or len(prices) < period * 3:
        return pd.Series(dtype=float)

    ema1 = prices.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    trix = ema3.pct_change() * 100
    return trix


def calculate_awesome_oscillator(high, low, short_period=5, long_period=34):
    """
    Calculate Awesome Oscillator

    > 0: Bullish momentum
    < 0: Bearish momentum
    """
    if any(x is None or len(x) < long_period for x in [high, low]):
        return pd.Series(dtype=float)

    midpoint = (high + low) / 2
    ao = midpoint.rolling(window=short_period).mean() - midpoint.rolling(window=long_period).mean()
    return ao


# =============================================================================
# 4. TREND INDICATORS
# =============================================================================

def calculate_adx(high, low, close, period=14):
    """
    Calculate Average Directional Index (ADX)

    ADX > 25: Strong trend
    ADX 20-25: Developing trend
    ADX < 20: Weak/no trend

    +DI > -DI: Bullish trend
    -DI > +DI: Bearish trend
    """
    if any(x is None or len(x) < period * 2 for x in [high, low, close]):
        empty = pd.Series(dtype=float)
        return empty, empty, empty

    # Calculate directional movement
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    # When both are positive, keep the larger one
    plus_dm[(plus_dm > 0) & (minus_dm > plus_dm)] = 0
    minus_dm[(minus_dm > 0) & (plus_dm > minus_dm)] = 0

    # Calculate ATR
    atr = calculate_atr(high, low, close, period)

    # Calculate directional indicators
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)

    # Calculate ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()

    return adx, plus_di, minus_di


def calculate_parabolic_sar(high, low, close, af=0.02, max_af=0.2):
    """
    Calculate Parabolic SAR

    Price > SAR: Bullish (SAR below price, acts as support)
    Price < SAR: Bearish (SAR above price, acts as resistance)
    """
    if any(x is None or len(x) < 5 for x in [high, low, close]):
        return pd.Series(dtype=float)

    length = len(close)
    psar = close.copy()
    psar_bull = True
    af_current = af
    ep = low.iloc[0]

    for i in range(2, length):
        if psar_bull:
            psar.iloc[i] = psar.iloc[i-1] + af_current * (ep - psar.iloc[i-1])
            psar.iloc[i] = min(psar.iloc[i], low.iloc[i-1], low.iloc[i-2])

            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af_current = min(af_current + af, max_af)

            if low.iloc[i] < psar.iloc[i]:
                psar_bull = False
                psar.iloc[i] = ep
                ep = low.iloc[i]
                af_current = af
        else:
            psar.iloc[i] = psar.iloc[i-1] + af_current * (ep - psar.iloc[i-1])
            psar.iloc[i] = max(psar.iloc[i], high.iloc[i-1], high.iloc[i-2])

            if low.iloc[i] < ep:
                ep = low.iloc[i]
                af_current = min(af_current + af, max_af)

            if high.iloc[i] > psar.iloc[i]:
                psar_bull = True
                psar.iloc[i] = ep
                ep = high.iloc[i]
                af_current = af

    return psar


def calculate_ichimoku(high, low, close, tenkan=9, kijun=26, senkou_b=52):
    """
    Calculate Ichimoku Cloud components

    Components:
    - Tenkan-sen (Conversion Line): Short-term trend
    - Kijun-sen (Base Line): Medium-term trend
    - Senkou Span A: Leading Span A
    - Senkou Span B: Leading Span B
    - Chikou Span: Lagging Span

    Price above cloud: Bullish
    Price below cloud: Bearish
    """
    if any(x is None or len(x) < senkou_b + kijun for x in [high, low, close]):
        return {}

    # Tenkan-sen (Conversion Line)
    tenkan_sen = (high.rolling(window=tenkan).max() + low.rolling(window=tenkan).min()) / 2

    # Kijun-sen (Base Line)
    kijun_sen = (high.rolling(window=kijun).max() + low.rolling(window=kijun).min()) / 2

    # Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)

    # Senkou Span B (Leading Span B)
    senkou_span_b = ((high.rolling(window=senkou_b).max() + low.rolling(window=senkou_b).min()) / 2).shift(kijun)

    # Chikou Span (Lagging Span)
    chikou_span = close.shift(-kijun)

    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }


# =============================================================================
# 5. MARKET SENTIMENT INDICATORS
# =============================================================================

def calculate_fear_greed_indicators(stock_data):
    """
    Calculate indicators related to market sentiment

    Based on available data, provides:
    - Short Interest Ratio (Days to Cover)
    - Short Interest Change
    - Insider Trading Signals
    """
    indicators = {}

    # Short Interest Analysis
    if stock_data.get('short_ratio'):
        indicators['short_ratio'] = stock_data['short_ratio']
        # Interpretation
        if stock_data['short_ratio'] > 10:
            indicators['short_squeeze_risk'] = 'High'
        elif stock_data['short_ratio'] > 5:
            indicators['short_squeeze_risk'] = 'Moderate'
        else:
            indicators['short_squeeze_risk'] = 'Low'

    if stock_data.get('short_percent_of_float'):
        indicators['short_percent'] = stock_data['short_percent_of_float']
        if stock_data['short_percent_of_float'] > 0.2:
            indicators['bearish_sentiment'] = 'High'
        elif stock_data['short_percent_of_float'] > 0.1:
            indicators['bearish_sentiment'] = 'Moderate'
        else:
            indicators['bearish_sentiment'] = 'Low'

    # Insider Activity (if available)
    if stock_data.get('held_percent_insiders'):
        indicators['insider_ownership'] = stock_data['held_percent_insiders']

    if stock_data.get('held_percent_institutions'):
        indicators['institutional_ownership'] = stock_data['held_percent_institutions']

    return indicators


def calculate_relative_strength(prices, benchmark_prices, period=63):
    """
    Calculate Relative Strength vs Benchmark

    > 1: Outperforming benchmark
    < 1: Underperforming benchmark
    """
    if prices is None or benchmark_prices is None or len(prices) < period:
        return pd.Series(dtype=float)

    aligned = pd.concat([prices, benchmark_prices], axis=1, join='inner').dropna()
    if len(aligned) < period:
        return pd.Series(dtype=float)

    stock = aligned.iloc[:, 0]
    bench = aligned.iloc[:, 1]

    rs = (stock / stock.shift(period)) / (bench / bench.shift(period))
    return rs


# =============================================================================
# 6. TIME-BASED ANALYSIS
# =============================================================================

def calculate_seasonality(prices, groupby='month'):
    """
    Calculate seasonal patterns

    Returns average return by month/quarter/day of week
    """
    if prices is None or len(prices) < 252:  # Need at least 1 year
        return {}

    returns = prices.pct_change().dropna()

    if groupby == 'month':
        seasonal = returns.groupby(returns.index.month).mean()
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        seasonal.index = labels[:len(seasonal)]
    elif groupby == 'quarter':
        seasonal = returns.groupby(returns.index.quarter).mean()
        labels = ['Q1', 'Q2', 'Q3', 'Q4']
        seasonal.index = labels[:len(seasonal)]
    elif groupby == 'dayofweek':
        seasonal = returns.groupby(returns.index.dayofweek).mean()
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        seasonal.index = labels[:len(seasonal)]
    else:
        return {}

    return seasonal.to_dict()


def calculate_earnings_momentum(prices, earnings_dates):
    """
    Calculate post-earnings price momentum

    Analyzes price movement around earnings announcements
    """
    if prices is None or earnings_dates is None or len(earnings_dates) == 0:
        return {}

    results = []
    for date in earnings_dates:
        if date in prices.index:
            idx = prices.index.get_loc(date)
            if idx > 5 and idx < len(prices) - 5:
                # 5-day return after earnings
                post_return = (prices.iloc[idx + 5] / prices.iloc[idx]) - 1
                results.append(post_return)

    if len(results) > 0:
        return {
            'avg_post_earnings_return': np.mean(results),
            'earnings_beat_rate': sum(1 for r in results if r > 0) / len(results),
            'n_earnings': len(results)
        }

    return {}


# =============================================================================
# COMPREHENSIVE TECHNICAL ANALYSIS
# =============================================================================

def calculate_all_technicals(ohlcv_data, include_extended=True):
    """
    Calculate all technical indicators from OHLCV data

    Args:
        ohlcv_data: DataFrame with columns: Open, High, Low, Close, Volume
        include_extended: Include extended indicators (Ichimoku, etc.)

    Returns:
        Dictionary with all calculated indicators
    """
    results = {}

    if ohlcv_data is None or len(ohlcv_data) < 20:
        return results

    close = ohlcv_data['Close']
    high = ohlcv_data['High']
    low = ohlcv_data['Low']
    volume = ohlcv_data['Volume']
    current_price = close.iloc[-1]

    # =========================================================================
    # RSI
    # =========================================================================
    rsi = calculate_rsi(close)
    results['rsi'] = rsi.iloc[-1] if len(rsi) > 0 and pd.notna(rsi.iloc[-1]) else np.nan
    results['rsi_oversold'] = results['rsi'] < 30 if pd.notna(results['rsi']) else False
    results['rsi_overbought'] = results['rsi'] > 70 if pd.notna(results['rsi']) else False
    results['rsi_signal'] = 'Oversold' if results['rsi_oversold'] else ('Overbought' if results['rsi_overbought'] else 'Neutral')

    # =========================================================================
    # MACD
    # =========================================================================
    macd, signal, hist = calculate_macd(close)
    results['macd'] = macd.iloc[-1] if len(macd) > 0 and pd.notna(macd.iloc[-1]) else np.nan
    results['macd_signal'] = signal.iloc[-1] if len(signal) > 0 and pd.notna(signal.iloc[-1]) else np.nan
    results['macd_histogram'] = hist.iloc[-1] if len(hist) > 0 and pd.notna(hist.iloc[-1]) else np.nan
    results['macd_bullish'] = results['macd'] > results['macd_signal'] if pd.notna(results['macd']) else False
    results['macd_crossover'] = 'Bullish' if results['macd_bullish'] else 'Bearish'

    # =========================================================================
    # Bollinger Bands
    # =========================================================================
    upper, middle, lower, percent_b, bandwidth = calculate_bollinger_bands(close)
    results['bb_upper'] = upper.iloc[-1] if len(upper) > 0 and pd.notna(upper.iloc[-1]) else np.nan
    results['bb_middle'] = middle.iloc[-1] if len(middle) > 0 and pd.notna(middle.iloc[-1]) else np.nan
    results['bb_lower'] = lower.iloc[-1] if len(lower) > 0 and pd.notna(lower.iloc[-1]) else np.nan
    results['bb_percent_b'] = percent_b.iloc[-1] if len(percent_b) > 0 and pd.notna(percent_b.iloc[-1]) else np.nan
    results['bb_bandwidth'] = bandwidth.iloc[-1] if len(bandwidth) > 0 and pd.notna(bandwidth.iloc[-1]) else np.nan

    # BB Position Signal
    if pd.notna(results['bb_percent_b']):
        if results['bb_percent_b'] > 1:
            results['bb_signal'] = 'Above Upper'
        elif results['bb_percent_b'] < 0:
            results['bb_signal'] = 'Below Lower'
        elif results['bb_percent_b'] > 0.8:
            results['bb_signal'] = 'Near Upper'
        elif results['bb_percent_b'] < 0.2:
            results['bb_signal'] = 'Near Lower'
        else:
            results['bb_signal'] = 'Middle'

    # =========================================================================
    # Moving Averages
    # =========================================================================
    mas = calculate_moving_averages(close)
    for ma_name, ma_series in mas.items():
        results[ma_name] = ma_series.iloc[-1] if len(ma_series) > 0 and pd.notna(ma_series.iloc[-1]) else np.nan

    # Price vs MAs
    for period in [20, 50, 200]:
        sma_key = f'sma_{period}'
        if sma_key in results and pd.notna(results[sma_key]):
            results[f'price_vs_{sma_key}'] = (current_price / results[sma_key] - 1)

    # Golden/Death Cross
    if pd.notna(results.get('sma_50')) and pd.notna(results.get('sma_200')):
        results['golden_cross'] = results['sma_50'] > results['sma_200']
        results['cross_signal'] = 'Golden Cross' if results['golden_cross'] else 'Death Cross'

    # =========================================================================
    # Support/Resistance
    # =========================================================================
    sr_levels = calculate_support_resistance(close)
    results['support'] = sr_levels.get('nearest_support', np.nan)
    results['resistance'] = sr_levels.get('nearest_resistance', np.nan)

    # Distance to support/resistance
    if pd.notna(results['support']):
        results['distance_to_support'] = (current_price - results['support']) / current_price
    if pd.notna(results['resistance']):
        results['distance_to_resistance'] = (results['resistance'] - current_price) / current_price

    # =========================================================================
    # ATR
    # =========================================================================
    atr = calculate_atr(high, low, close)
    results['atr'] = atr.iloc[-1] if len(atr) > 0 and pd.notna(atr.iloc[-1]) else np.nan
    results['atr_percent'] = (results['atr'] / current_price * 100) if pd.notna(results['atr']) else np.nan

    # =========================================================================
    # Stochastic
    # =========================================================================
    k, d = calculate_stochastic(high, low, close)
    results['stoch_k'] = k.iloc[-1] if len(k) > 0 and pd.notna(k.iloc[-1]) else np.nan
    results['stoch_d'] = d.iloc[-1] if len(d) > 0 and pd.notna(d.iloc[-1]) else np.nan
    if pd.notna(results['stoch_k']):
        results['stoch_signal'] = 'Oversold' if results['stoch_k'] < 20 else ('Overbought' if results['stoch_k'] > 80 else 'Neutral')

    # =========================================================================
    # Williams %R
    # =========================================================================
    williams = calculate_williams_r(high, low, close)
    results['williams_r'] = williams.iloc[-1] if len(williams) > 0 and pd.notna(williams.iloc[-1]) else np.nan

    # =========================================================================
    # CCI
    # =========================================================================
    cci = calculate_cci(high, low, close)
    results['cci'] = cci.iloc[-1] if len(cci) > 0 and pd.notna(cci.iloc[-1]) else np.nan

    # =========================================================================
    # Volume Indicators
    # =========================================================================
    results['volume'] = volume.iloc[-1]
    results['volume_avg_20'] = volume.rolling(window=20).mean().iloc[-1] if len(volume) >= 20 else np.nan

    vol_ratio = calculate_volume_ratio(volume)
    results['volume_ratio'] = vol_ratio.iloc[-1] if isinstance(vol_ratio, pd.Series) and len(vol_ratio) > 0 else np.nan

    # OBV
    obv = calculate_obv(close, volume)
    results['obv'] = obv.iloc[-1] if len(obv) > 0 else np.nan
    if len(obv) > 20:
        results['obv_trend'] = 'Up' if obv.iloc[-1] > obv.iloc[-20] else 'Down'

    # MFI
    mfi = calculate_mfi(high, low, close, volume)
    results['mfi'] = mfi.iloc[-1] if len(mfi) > 0 and pd.notna(mfi.iloc[-1]) else np.nan

    # VWAP
    vwap = calculate_vwap(high, low, close, volume)
    results['vwap'] = vwap.iloc[-1] if len(vwap) > 0 and pd.notna(vwap.iloc[-1]) else np.nan
    results['price_vs_vwap'] = (current_price / results['vwap'] - 1) if pd.notna(results['vwap']) else np.nan

    # Chaikin Money Flow
    cmf = calculate_chaikin_money_flow(high, low, close, volume)
    results['cmf'] = cmf.iloc[-1] if len(cmf) > 0 and pd.notna(cmf.iloc[-1]) else np.nan

    # =========================================================================
    # ADX
    # =========================================================================
    adx, plus_di, minus_di = calculate_adx(high, low, close)
    results['adx'] = adx.iloc[-1] if len(adx) > 0 and pd.notna(adx.iloc[-1]) else np.nan
    results['plus_di'] = plus_di.iloc[-1] if len(plus_di) > 0 and pd.notna(plus_di.iloc[-1]) else np.nan
    results['minus_di'] = minus_di.iloc[-1] if len(minus_di) > 0 and pd.notna(minus_di.iloc[-1]) else np.nan
    results['strong_trend'] = results['adx'] > 25 if pd.notna(results['adx']) else False

    if pd.notna(results['adx']):
        if results['adx'] > 50:
            results['trend_strength'] = 'Very Strong'
        elif results['adx'] > 25:
            results['trend_strength'] = 'Strong'
        else:
            results['trend_strength'] = 'Weak'

    # =========================================================================
    # Momentum
    # =========================================================================
    momentum = calculate_momentum(close)
    results['momentum_10'] = momentum.iloc[-1] if len(momentum) > 0 and pd.notna(momentum.iloc[-1]) else np.nan

    roc = calculate_roc(close)
    results['roc_10'] = roc.iloc[-1] if len(roc) > 0 and pd.notna(roc.iloc[-1]) else np.nan

    # =========================================================================
    # Extended Indicators
    # =========================================================================
    if include_extended:
        # Parabolic SAR
        psar = calculate_parabolic_sar(high, low, close)
        results['psar'] = psar.iloc[-1] if len(psar) > 0 and pd.notna(psar.iloc[-1]) else np.nan
        if pd.notna(results['psar']):
            results['psar_signal'] = 'Bullish' if current_price > results['psar'] else 'Bearish'

        # Ichimoku
        ichimoku = calculate_ichimoku(high, low, close)
        if ichimoku:
            for key, series in ichimoku.items():
                if series is not None and len(series) > 0:
                    results[f'ichimoku_{key}'] = series.iloc[-1] if pd.notna(series.iloc[-1]) else np.nan

        # Awesome Oscillator
        ao = calculate_awesome_oscillator(high, low)
        results['ao'] = ao.iloc[-1] if len(ao) > 0 and pd.notna(ao.iloc[-1]) else np.nan

        # Pivot Points
        pivots = calculate_pivot_points(high, low, close)
        for key, value in pivots.items():
            results[f'pivot_{key}'] = value

    return results


def get_technical_signal(technicals):
    """
    Generate overall technical signal from indicators

    Returns:
        Signal: 'Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'
        Score: Numeric score from -100 to +100
    """
    buy_signals = 0
    sell_signals = 0

    # -------------------------------------------------------------------------
    # RSI (weight: 15)
    # -------------------------------------------------------------------------
    rsi = technicals.get('rsi')
    if pd.notna(rsi):
        if rsi < 30:
            buy_signals += 15
        elif rsi < 40:
            buy_signals += 5
        elif rsi > 70:
            sell_signals += 15
        elif rsi > 60:
            sell_signals += 5

    # -------------------------------------------------------------------------
    # MACD (weight: 15)
    # -------------------------------------------------------------------------
    if technicals.get('macd_bullish'):
        buy_signals += 10
        if technicals.get('macd_histogram', 0) > 0:
            buy_signals += 5
    else:
        sell_signals += 10
        if technicals.get('macd_histogram', 0) < 0:
            sell_signals += 5

    # -------------------------------------------------------------------------
    # Moving Averages (weight: 20)
    # -------------------------------------------------------------------------
    if technicals.get('golden_cross'):
        buy_signals += 15
    elif technicals.get('golden_cross') is False:
        sell_signals += 15

    price_vs_200 = technicals.get('price_vs_sma_200', 0)
    if price_vs_200 and price_vs_200 > 0.05:
        buy_signals += 5
    elif price_vs_200 and price_vs_200 < -0.05:
        sell_signals += 5

    # -------------------------------------------------------------------------
    # Bollinger Bands (weight: 10)
    # -------------------------------------------------------------------------
    bb_b = technicals.get('bb_percent_b')
    if pd.notna(bb_b):
        if bb_b < 0.1:
            buy_signals += 10  # Near lower band
        elif bb_b < 0.2:
            buy_signals += 5
        elif bb_b > 0.9:
            sell_signals += 10  # Near upper band
        elif bb_b > 0.8:
            sell_signals += 5

    # -------------------------------------------------------------------------
    # Stochastic (weight: 10)
    # -------------------------------------------------------------------------
    stoch_k = technicals.get('stoch_k')
    if pd.notna(stoch_k):
        if stoch_k < 20:
            buy_signals += 10
        elif stoch_k > 80:
            sell_signals += 10

    # -------------------------------------------------------------------------
    # ADX (weight: 10)
    # -------------------------------------------------------------------------
    adx = technicals.get('adx')
    plus_di = technicals.get('plus_di')
    minus_di = technicals.get('minus_di')
    if all(pd.notna(x) for x in [adx, plus_di, minus_di]):
        if adx > 25:  # Strong trend
            if plus_di > minus_di:
                buy_signals += 10
            else:
                sell_signals += 10

    # -------------------------------------------------------------------------
    # Volume (weight: 10)
    # -------------------------------------------------------------------------
    vol_ratio = technicals.get('volume_ratio')
    if pd.notna(vol_ratio):
        price_change = technicals.get('roc_10', 0)
        if vol_ratio > 1.5 and price_change > 0:
            buy_signals += 10  # High volume up move
        elif vol_ratio > 1.5 and price_change < 0:
            sell_signals += 10  # High volume down move

    # -------------------------------------------------------------------------
    # Money Flow (weight: 10)
    # -------------------------------------------------------------------------
    mfi = technicals.get('mfi')
    if pd.notna(mfi):
        if mfi < 20:
            buy_signals += 10
        elif mfi > 80:
            sell_signals += 10

    # -------------------------------------------------------------------------
    # Calculate final score and signal
    # -------------------------------------------------------------------------
    net_score = buy_signals - sell_signals

    if net_score >= 40:
        signal = 'Strong Buy'
    elif net_score >= 20:
        signal = 'Buy'
    elif net_score <= -40:
        signal = 'Strong Sell'
    elif net_score <= -20:
        signal = 'Sell'
    else:
        signal = 'Neutral'

    return signal, net_score
