"""
Technical Analysis Module
Implements technical indicators and market sentiment metrics
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# PRICE-BASED TECHNICAL INDICATORS
# =============================================================================

def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI)
    RSI > 70: Overbought
    RSI < 30: Oversold
    """
    if len(prices) < period + 1:
        return pd.Series(index=prices.index, dtype=float)

    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    Returns: MACD line, Signal line, Histogram
    """
    if len(prices) < slow + signal:
        empty = pd.Series(index=prices.index, dtype=float)
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
    Returns: Upper band, Middle band (SMA), Lower band, %B, Bandwidth
    """
    if len(prices) < period:
        empty = pd.Series(index=prices.index, dtype=float)
        return empty, empty, empty, empty, empty

    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    # %B indicates where price is relative to bands (0 = lower, 1 = upper)
    percent_b = (prices - lower) / (upper - lower)

    # Bandwidth indicates volatility
    bandwidth = (upper - lower) / middle

    return upper, middle, lower, percent_b, bandwidth


def calculate_moving_averages(prices, periods=[20, 50, 100, 200]):
    """Calculate Simple and Exponential Moving Averages"""
    mas = {}
    for period in periods:
        if len(prices) >= period:
            mas[f'sma_{period}'] = prices.rolling(window=period).mean()
            mas[f'ema_{period}'] = prices.ewm(span=period, adjust=False).mean()
        else:
            mas[f'sma_{period}'] = pd.Series(index=prices.index, dtype=float)
            mas[f'ema_{period}'] = pd.Series(index=prices.index, dtype=float)
    return mas


def calculate_support_resistance(prices, window=20):
    """
    Calculate Support and Resistance levels
    Uses local minima/maxima
    """
    if len(prices) < window * 2:
        return np.nan, np.nan

    # Find recent peaks and troughs
    rolling_max = prices.rolling(window=window, center=True).max()
    rolling_min = prices.rolling(window=window, center=True).min()

    peaks = prices[prices == rolling_max].dropna().unique()
    troughs = prices[prices == rolling_min].dropna().unique()

    current_price = prices.iloc[-1]

    # Resistance: nearest peak above current price
    resistance_levels = peaks[peaks > current_price]
    resistance = resistance_levels.min() if len(resistance_levels) > 0 else np.nan

    # Support: nearest trough below current price
    support_levels = troughs[troughs < current_price]
    support = support_levels.max() if len(support_levels) > 0 else np.nan

    return support, resistance


def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range (volatility indicator)"""
    if len(close) < period + 1:
        return pd.Series(index=close.index, dtype=float)

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def calculate_stochastic(high, low, close, k_period=14, d_period=3):
    """
    Calculate Stochastic Oscillator (%K and %D)
    > 80: Overbought
    < 20: Oversold
    """
    if len(close) < k_period:
        empty = pd.Series(index=close.index, dtype=float)
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
    if len(close) < period:
        return pd.Series(index=close.index, dtype=float)

    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()

    williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)

    return williams_r


def calculate_cci(high, low, close, period=20):
    """
    Calculate Commodity Channel Index
    > 100: Overbought/Strong uptrend
    < -100: Oversold/Strong downtrend
    """
    if len(close) < period:
        return pd.Series(index=close.index, dtype=float)

    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean()
    )

    cci = (typical_price - sma_tp) / (0.015 * mean_deviation)

    return cci


# =============================================================================
# VOLUME-BASED INDICATORS
# =============================================================================

def calculate_obv(close, volume):
    """Calculate On-Balance Volume"""
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_vwap(high, low, close, volume):
    """Calculate Volume-Weighted Average Price"""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap


def calculate_volume_ratio(volume, period=20):
    """Calculate current volume vs average volume"""
    if len(volume) < period:
        return np.nan
    avg_volume = volume.rolling(window=period).mean()
    return volume / avg_volume


def calculate_mfi(high, low, close, volume, period=14):
    """
    Calculate Money Flow Index (Volume-weighted RSI)
    > 80: Overbought
    < 20: Oversold
    """
    if len(close) < period + 1:
        return pd.Series(index=close.index, dtype=float)

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
    """Calculate Accumulation/Distribution Line"""
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)
    ad = (clv * volume).cumsum()
    return ad


# =============================================================================
# MOMENTUM INDICATORS
# =============================================================================

def calculate_momentum(prices, period=10):
    """Calculate price momentum"""
    return prices - prices.shift(period)


def calculate_roc(prices, period=10):
    """Calculate Rate of Change"""
    return ((prices / prices.shift(period)) - 1) * 100


def calculate_trix(prices, period=15):
    """Calculate TRIX (Triple Exponential Moving Average)"""
    ema1 = prices.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    trix = ema3.pct_change() * 100
    return trix


# =============================================================================
# TREND INDICATORS
# =============================================================================

def calculate_adx(high, low, close, period=14):
    """
    Calculate Average Directional Index
    > 25: Strong trend
    < 20: Weak/no trend
    """
    if len(close) < period * 2:
        return pd.Series(index=close.index, dtype=float), pd.Series(index=close.index, dtype=float), pd.Series(index=close.index, dtype=float)

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr = calculate_atr(high, low, close, 1)

    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() /
                     tr.ewm(span=period, adjust=False).mean())
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() /
                      tr.ewm(span=period, adjust=False).mean())

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()

    return adx, plus_di, minus_di


def calculate_parabolic_sar(high, low, close, af=0.02, max_af=0.2):
    """Calculate Parabolic SAR"""
    if len(close) < 5:
        return pd.Series(index=close.index, dtype=float)

    psar = close.copy()
    psar_up = True
    af_current = af
    ep = low.iloc[0]

    for i in range(2, len(close)):
        if psar_up:
            psar.iloc[i] = psar.iloc[i-1] + af_current * (ep - psar.iloc[i-1])
            psar.iloc[i] = min(psar.iloc[i], low.iloc[i-1], low.iloc[i-2])
            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af_current = min(af_current + af, max_af)
            if low.iloc[i] < psar.iloc[i]:
                psar_up = False
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
                psar_up = True
                psar.iloc[i] = ep
                ep = high.iloc[i]
                af_current = af

    return psar


# =============================================================================
# COMPREHENSIVE TECHNICAL ANALYSIS
# =============================================================================

def calculate_all_technicals(ohlcv_data):
    """
    Calculate all technical indicators from OHLCV data
    ohlcv_data should be a DataFrame with columns: Open, High, Low, Close, Volume
    """
    results = {}

    close = ohlcv_data['Close']
    high = ohlcv_data['High']
    low = ohlcv_data['Low']
    volume = ohlcv_data['Volume']

    # RSI
    rsi = calculate_rsi(close)
    results['rsi'] = rsi.iloc[-1] if len(rsi) > 0 else np.nan
    results['rsi_oversold'] = rsi.iloc[-1] < 30 if pd.notna(results['rsi']) else False
    results['rsi_overbought'] = rsi.iloc[-1] > 70 if pd.notna(results['rsi']) else False

    # MACD
    macd, signal, hist = calculate_macd(close)
    results['macd'] = macd.iloc[-1] if len(macd) > 0 else np.nan
    results['macd_signal'] = signal.iloc[-1] if len(signal) > 0 else np.nan
    results['macd_histogram'] = hist.iloc[-1] if len(hist) > 0 else np.nan
    results['macd_bullish'] = (macd.iloc[-1] > signal.iloc[-1]) if pd.notna(results['macd']) else False

    # Bollinger Bands
    upper, middle, lower, percent_b, bandwidth = calculate_bollinger_bands(close)
    results['bb_upper'] = upper.iloc[-1] if len(upper) > 0 else np.nan
    results['bb_middle'] = middle.iloc[-1] if len(middle) > 0 else np.nan
    results['bb_lower'] = lower.iloc[-1] if len(lower) > 0 else np.nan
    results['bb_percent_b'] = percent_b.iloc[-1] if len(percent_b) > 0 else np.nan
    results['bb_bandwidth'] = bandwidth.iloc[-1] if len(bandwidth) > 0 else np.nan

    # Moving Averages
    mas = calculate_moving_averages(close)
    results['sma_20'] = mas['sma_20'].iloc[-1] if len(mas['sma_20']) > 0 else np.nan
    results['sma_50'] = mas['sma_50'].iloc[-1] if len(mas['sma_50']) > 0 else np.nan
    results['sma_200'] = mas['sma_200'].iloc[-1] if len(mas['sma_200']) > 0 else np.nan
    results['ema_20'] = mas['ema_20'].iloc[-1] if len(mas['ema_20']) > 0 else np.nan

    # Price vs MAs
    current_price = close.iloc[-1]
    results['price_vs_sma_20'] = (current_price / results['sma_20'] - 1) if pd.notna(results['sma_20']) else np.nan
    results['price_vs_sma_50'] = (current_price / results['sma_50'] - 1) if pd.notna(results['sma_50']) else np.nan
    results['price_vs_sma_200'] = (current_price / results['sma_200'] - 1) if pd.notna(results['sma_200']) else np.nan

    # Golden/Death Cross
    if pd.notna(results['sma_50']) and pd.notna(results['sma_200']):
        results['golden_cross'] = results['sma_50'] > results['sma_200']
    else:
        results['golden_cross'] = None

    # Support/Resistance
    support, resistance = calculate_support_resistance(close)
    results['support'] = support
    results['resistance'] = resistance

    # ATR
    atr = calculate_atr(high, low, close)
    results['atr'] = atr.iloc[-1] if len(atr) > 0 else np.nan
    results['atr_percent'] = (results['atr'] / current_price * 100) if pd.notna(results['atr']) else np.nan

    # Stochastic
    k, d = calculate_stochastic(high, low, close)
    results['stoch_k'] = k.iloc[-1] if len(k) > 0 else np.nan
    results['stoch_d'] = d.iloc[-1] if len(d) > 0 else np.nan

    # Williams %R
    williams = calculate_williams_r(high, low, close)
    results['williams_r'] = williams.iloc[-1] if len(williams) > 0 else np.nan

    # CCI
    cci = calculate_cci(high, low, close)
    results['cci'] = cci.iloc[-1] if len(cci) > 0 else np.nan

    # Volume
    results['volume'] = volume.iloc[-1]
    vol_ratio = calculate_volume_ratio(volume)
    results['volume_ratio'] = vol_ratio.iloc[-1] if isinstance(vol_ratio, pd.Series) else vol_ratio

    # OBV
    obv = calculate_obv(close, volume)
    results['obv'] = obv.iloc[-1] if len(obv) > 0 else np.nan
    results['obv_trend'] = 'up' if obv.iloc[-1] > obv.iloc[-20] else 'down' if len(obv) > 20 else 'neutral'

    # MFI
    mfi = calculate_mfi(high, low, close, volume)
    results['mfi'] = mfi.iloc[-1] if len(mfi) > 0 else np.nan

    # VWAP
    vwap = calculate_vwap(high, low, close, volume)
    results['vwap'] = vwap.iloc[-1] if len(vwap) > 0 else np.nan
    results['price_vs_vwap'] = (current_price / results['vwap'] - 1) if pd.notna(results['vwap']) else np.nan

    # ADX
    adx, plus_di, minus_di = calculate_adx(high, low, close)
    results['adx'] = adx.iloc[-1] if len(adx) > 0 else np.nan
    results['plus_di'] = plus_di.iloc[-1] if len(plus_di) > 0 else np.nan
    results['minus_di'] = minus_di.iloc[-1] if len(minus_di) > 0 else np.nan
    results['strong_trend'] = results['adx'] > 25 if pd.notna(results['adx']) else False

    # Momentum
    momentum = calculate_momentum(close)
    results['momentum_10'] = momentum.iloc[-1] if len(momentum) > 0 else np.nan

    # ROC
    roc = calculate_roc(close)
    results['roc_10'] = roc.iloc[-1] if len(roc) > 0 else np.nan

    return results


def get_technical_signal(technicals):
    """
    Generate overall technical signal from indicators
    Returns: 'strong_buy', 'buy', 'neutral', 'sell', 'strong_sell'
    """
    buy_signals = 0
    sell_signals = 0

    # RSI
    if technicals.get('rsi_oversold'):
        buy_signals += 2
    elif technicals.get('rsi_overbought'):
        sell_signals += 2

    # MACD
    if technicals.get('macd_bullish'):
        buy_signals += 1
    else:
        sell_signals += 1

    # Moving Averages
    if technicals.get('golden_cross'):
        buy_signals += 2
    elif technicals.get('golden_cross') is False:
        sell_signals += 2

    price_vs_200 = technicals.get('price_vs_sma_200', 0)
    if price_vs_200 and price_vs_200 > 0.1:
        buy_signals += 1
    elif price_vs_200 and price_vs_200 < -0.1:
        sell_signals += 1

    # Bollinger
    bb_b = technicals.get('bb_percent_b', 0.5)
    if bb_b and bb_b < 0.2:
        buy_signals += 1
    elif bb_b and bb_b > 0.8:
        sell_signals += 1

    # Stochastic
    stoch_k = technicals.get('stoch_k', 50)
    if stoch_k and stoch_k < 20:
        buy_signals += 1
    elif stoch_k and stoch_k > 80:
        sell_signals += 1

    # Calculate signal
    net_signal = buy_signals - sell_signals

    if net_signal >= 4:
        return 'strong_buy'
    elif net_signal >= 2:
        return 'buy'
    elif net_signal <= -4:
        return 'strong_sell'
    elif net_signal <= -2:
        return 'sell'
    else:
        return 'neutral'
