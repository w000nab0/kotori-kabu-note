#!/usr/bin/env python3
"""株価データ取得テスト"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# モジュールパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.stock_service import StockService

def test_yfinance_basic():
    """基本的なyfinanceテスト"""
    print("=== yfinance基本テスト ===")
    
    # 日本株のテスト
    stock_code = "7203.T"
    ticker = yf.Ticker(stock_code)
    
    try:
        # 基本情報を取得
        info = ticker.info
        print(f"Stock: {info.get('longName', 'N/A')}")
        print(f"Market: {info.get('market', 'N/A')}")
        print(f"Currency: {info.get('currency', 'N/A')}")
        
        # 1ヶ月分の履歴データを取得
        hist = ticker.history(period="1mo")
        print(f"\nHistorical data shape: {hist.shape}")
        if not hist.empty:
            print(f"Date range: {hist.index[0]} to {hist.index[-1]}")
            
            # 最新の価格データを表示
            latest = hist.iloc[-1]
            print(f"\nLatest data:")
            print(f"Close: {latest['Close']:.2f} JPY")
            print(f"Volume: {latest['Volume']:,}")
            
            # テクニカル指標計算のテスト
            print(f"\nTechnical indicators calculation test:")
            close_prices = hist['Close']
            
            # SMA計算
            if len(close_prices) >= 25:
                sma_25 = close_prices.rolling(25).mean().iloc[-1]
                print(f"SMA 25: {sma_25:.2f}")
            
            # RSI計算
            if len(close_prices) >= 14:
                delta = close_prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                print(f"RSI 14: {rsi.iloc[-1]:.2f}")
            
            print("✅ yfinance基本テスト成功!")
            return True
        else:
            print("❌ データが取得できませんでした")
            return False
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_stock_service():
    """StockServiceクラスのテスト"""
    print("\n=== StockServiceテスト ===")
    
    try:
        # 株価データ取得テスト
        print("1. 株価データ取得テスト")
        stock_code = "7203"
        period = "1M"
        
        price_data = StockService.get_stock_price_data(stock_code, period)
        print(f"Stock: {stock_code}")
        print(f"Period: {period}")
        print(f"Data points: {len(price_data.data)}")
        
        if price_data.data:
            latest = price_data.data[-1]
            print(f"Latest Close: {latest.close:.2f}")
            print(f"Latest Volume: {latest.volume:,}")
        
        # テクニカル指標計算テスト
        print("\n2. テクニカル指標計算テスト")
        try:
            indicators = StockService.calculate_technical_indicators(price_data.data)
            print(f"SMA 25: {indicators.sma_25:.2f if indicators.sma_25 is not None else 'N/A'}")
            print(f"SMA 75: {indicators.sma_75:.2f if indicators.sma_75 is not None else 'N/A'}")
            print(f"RSI 14: {indicators.rsi_14:.2f if indicators.rsi_14 is not None else 'N/A'}")
            print(f"MACD: {indicators.macd_line:.3f if indicators.macd_line is not None else 'N/A'}")
        except Exception as e:
            print(f"テクニカル指標計算エラー: {e}")
            print(f"indicators: {indicators if 'indicators' in locals() else 'N/A'}")
        
        # 検索機能テスト
        print("\n3. 検索機能テスト")
        search_results = StockService.search_stocks("トヨタ", 5)
        print(f"Search results for 'トヨタ': {len(search_results)}")
        for stock in search_results:
            print(f"  - {stock.code}: {stock.name} ({stock.sector})")
        
        print("✅ StockServiceテスト成功!")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_multiple_stocks():
    """複数銘柄のテスト"""
    print("\n=== 複数銘柄テスト ===")
    
    test_stocks = ["7203", "6758", "9984", "6861"]
    
    for stock_code in test_stocks:
        try:
            print(f"\nTesting {stock_code}...")
            price_data = StockService.get_stock_price_data(stock_code, "1M")
            
            if price_data.data:
                latest = price_data.data[-1]
                print(f"  ✅ {stock_code}: {latest.close:.2f} (Vol: {latest.volume:,})")
            else:
                print(f"  ❌ {stock_code}: データなし")
                
        except Exception as e:
            print(f"  ❌ {stock_code}: エラー - {str(e)}")
    
    print("✅ 複数銘柄テスト完了!")

if __name__ == "__main__":
    print("株価データ取得テスト開始...")
    print("=" * 50)
    
    # 基本テスト
    basic_success = test_yfinance_basic()
    
    # サービステスト
    service_success = test_stock_service()
    
    # 複数銘柄テスト
    test_multiple_stocks()
    
    print("\n" + "=" * 50)
    print("テスト結果:")
    print(f"基本テスト: {'✅ 成功' if basic_success else '❌ 失敗'}")
    print(f"サービステスト: {'✅ 成功' if service_success else '❌ 失敗'}")
    print("=" * 50)