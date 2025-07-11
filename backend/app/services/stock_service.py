import yfinance as yf
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import Stock, StockPriceCache
from app.models.stock import StockPriceData, StockPriceResponse, TechnicalIndicators
import json

class StockService:
    # 日本株の主要銘柄リスト（MVP版）
    POPULAR_STOCKS = [
        {"code": "7203", "name": "トヨタ自動車", "sector": "自動車"},
        {"code": "6758", "name": "ソニーグループ", "sector": "電気機器"},
        {"code": "9984", "name": "ソフトバンクグループ", "sector": "情報・通信業"},
        {"code": "6861", "name": "キーエンス", "sector": "電気機器"},
        {"code": "8306", "name": "三菱UFJフィナンシャル・グループ", "sector": "銀行業"},
        {"code": "4519", "name": "中外製薬", "sector": "医薬品"},
        {"code": "6098", "name": "リクルートホールディングス", "sector": "サービス業"},
        {"code": "9432", "name": "日本電信電話", "sector": "情報・通信業"},
        {"code": "6954", "name": "ファナック", "sector": "電気機器"},
        {"code": "8035", "name": "東京エレクトロン", "sector": "電気機器"}
    ]
    
    @staticmethod
    def search_stocks(query: str, limit: int = 10) -> List[Stock]:
        """銘柄検索"""
        # MVP版では静的リストから検索
        results = []
        query_lower = query.lower()
        
        for stock_data in StockService.POPULAR_STOCKS:
            if (query_lower in stock_data["code"].lower() or 
                query_lower in stock_data["name"].lower()):
                results.append(Stock(
                    code=stock_data["code"],
                    name=stock_data["name"],
                    sector=stock_data["sector"],
                    market="TSE",
                    is_active=True
                ))
                
        return results[:limit]
    
    @staticmethod
    def get_stock_price_data(stock_code: str, period: str = "1M") -> StockPriceResponse:
        """株価データ取得"""
        # MVP版：ネットワーク問題のためモックデータを返す
        # 本番環境では実際のyfinanceデータを使用する予定
        
        try:
            # 期間マッピング（テクニカル指標計算のため最低75日は確保）
            period_mapping = {
                "1W": 80,   # 1週間でも過去データを含めて80日分
                "1M": 90,   # 1ヶ月でも過去データを含めて90日分
                "3M": 120,  # 3ヶ月で120日分
                "6M": 180,  # 6ヶ月で180日分
                "1Y": 365   # 1年で365日分
            }
            
            days = period_mapping.get(period, 30)
            
            # モックデータ生成（実際の株価に近い値）
            stock_mock_data = {
                "7203": {"base_price": 3420, "name": "トヨタ自動車"},
                "6758": {"base_price": 13850, "name": "ソニーグループ"}, 
                "9984": {"base_price": 7890, "name": "ソフトバンクG"},
                "6861": {"base_price": 52300, "name": "キーエンス"}
            }
            
            base_price = stock_mock_data.get(stock_code, {"base_price": 1000})["base_price"]
            
            # 日付とモック価格データ生成
            price_data = []
            current_date = datetime.now() - timedelta(days=days)
            current_price = base_price
            
            for i in range(days):
                # 小さなランダム変動をシミュレート
                import random
                change_pct = random.uniform(-0.03, 0.03)  # -3%から+3%の変動
                
                open_price = current_price
                high_price = open_price * (1 + abs(change_pct) * 0.5)
                low_price = open_price * (1 - abs(change_pct) * 0.5)
                close_price = open_price * (1 + change_pct)
                volume = random.randint(1000000, 5000000)
                
                price_data.append(StockPriceData(
                    time=current_date.strftime("%Y-%m-%d"),
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=volume
                ))
                
                current_price = close_price
                current_date += timedelta(days=1)
            
            return StockPriceResponse(
                stock_code=stock_code,
                period=period,
                data=price_data,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {stock_code}: {str(e)}")
    
    @staticmethod
    def calculate_technical_indicators(price_data: List[StockPriceData]) -> TechnicalIndicators:
        """テクニカル指標計算"""
        if len(price_data) < 75:  # 75日分のデータが必要
            return TechnicalIndicators()
        
        # DataFrameに変換
        df = pd.DataFrame([{
            'close': data.close,
            'volume': data.volume or 0
        } for data in price_data])
        
        indicators = TechnicalIndicators()
        
        try:
            # SMA計算
            if len(df) >= 25:
                indicators.sma_25 = float(df['close'].rolling(25).mean().iloc[-1])
            if len(df) >= 75:
                indicators.sma_75 = float(df['close'].rolling(75).mean().iloc[-1])
            
            # RSI計算（14日）
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators.rsi_14 = float(rsi.iloc[-1])
            
            # MACD計算
            if len(df) >= 26:
                ema12 = df['close'].ewm(span=12).mean()
                ema26 = df['close'].ewm(span=26).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9).mean()
                histogram = macd_line - signal_line
                
                indicators.macd_line = float(macd_line.iloc[-1])
                indicators.macd_signal = float(signal_line.iloc[-1])
                indicators.macd_histogram = float(histogram.iloc[-1])
            
            # 出来高SMA
            if len(df) >= 25:
                indicators.volume_sma_25 = float(df['volume'].rolling(25).mean().iloc[-1])
                
        except Exception as e:
            print(f"Error calculating indicators: {e}")
        
        return indicators
    
    @staticmethod
    def get_cached_price_data(db: Session, stock_code: str, period: str) -> Optional[StockPriceResponse]:
        """キャッシュされた株価データ取得"""
        cache_key = f"{stock_code}_{period}"
        cached = db.query(StockPriceCache).filter(
            StockPriceCache.stock_code == cache_key,
            StockPriceCache.expires_at > datetime.utcnow()
        ).first()
        
        if cached:
            try:
                data = json.loads(cached.price_data)
                return StockPriceResponse(**data)
            except Exception:
                pass
        return None
    
    @staticmethod
    def cache_price_data(db: Session, stock_code: str, period: str, data: StockPriceResponse):
        """株価データをキャッシュ"""
        cache_key = f"{stock_code}_{period}"
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        # 既存キャッシュ削除
        db.query(StockPriceCache).filter(
            StockPriceCache.stock_code == cache_key
        ).delete()
        
        # 新しいキャッシュ作成
        cache_entry = StockPriceCache(
            stock_code=cache_key,
            price_data=data.model_dump_json(),
            expires_at=expires_at
        )
        
        db.add(cache_entry)
        db.commit()