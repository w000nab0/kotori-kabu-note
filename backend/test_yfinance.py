#!/usr/bin/env python3
"""Test yfinance ticker formats"""

import yfinance as yf

# Test different ticker formats for Japanese stocks
test_symbols = [
    '7203.T',    # Tokyo Stock Exchange format
    '7203.TO',   # Alternative format
    'TM',        # ADR symbol (Toyota Motor)
    '7203'       # Plain code
]

for symbol in test_symbols:
    print(f"\nTesting {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d')
        print(f"Data shape: {hist.shape}")
        if not hist.empty:
            print("SUCCESS! Found data:")
            print(hist.tail(2))
            print(f"Latest price: {hist['Close'].iloc[-1]:.2f}")
        else:
            print("No data found")
    except Exception as e:
        print(f"Error: {e}")