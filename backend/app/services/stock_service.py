import yfinance as yf
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import Stock, StockPriceCache
from app.models.stock import StockPriceData, StockPriceResponse, TechnicalIndicators
import json

class StockService:
    # 日本株の主要銘柄リスト（拡張版）
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
        {"code": "8035", "name": "東京エレクトロン", "sector": "電気機器"},
        {"code": "9983", "name": "ファーストリテイリング", "sector": "小売業"},
        {"code": "4502", "name": "武田薬品工業", "sector": "医薬品"},
        {"code": "9433", "name": "KDDI", "sector": "情報・通信業"},
        {"code": "6501", "name": "日立製作所", "sector": "電気機器"},
        {"code": "8316", "name": "三井住友フィナンシャルグループ", "sector": "銀行業"},
        {"code": "7201", "name": "日産自動車", "sector": "自動車"},
        {"code": "6752", "name": "パナソニック ホールディングス", "sector": "電気機器"},
        {"code": "8267", "name": "イオン", "sector": "小売業"},
        {"code": "4568", "name": "第一三共", "sector": "医薬品"},
        {"code": "8802", "name": "三菱地所", "sector": "不動産業"}
    ]
    
    @staticmethod
    def search_stocks(query: str, limit: int = 10) -> List[Stock]:
        """銘柄検索（データベース+静的リスト）"""
        # まずは静的リストから検索（フォールバック）
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
    def search_stocks_with_db(db: Session, query: str, limit: int = 10) -> List[Stock]:
        """データベースを使用した銘柄検索"""
        try:
            # データベースから検索
            from sqlalchemy import or_
            stocks = db.query(Stock).filter(
                Stock.is_active == True
            ).filter(
                or_(
                    Stock.code.ilike(f"%{query}%"),
                    Stock.name.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            # データベースに結果がない場合は静的リストから検索
            if not stocks:
                return StockService.search_stocks(query, limit)
            
            return stocks
            
        except Exception as e:
            print(f"Database search error: {str(e)}")
            # エラーの場合は静的リストから検索
            return StockService.search_stocks(query, limit)
    
    @staticmethod
    def get_popular_stocks(db: Session, limit: int = 20) -> List[Stock]:
        """人気銘柄取得"""
        try:
            # データベースから人気銘柄を取得
            popular_codes = [stock["code"] for stock in StockService.POPULAR_STOCKS[:limit]]
            stocks = db.query(Stock).filter(
                Stock.code.in_(popular_codes),
                Stock.is_active == True
            ).all()
            
            # データベースに結果がない場合は静的リストから作成
            if not stocks:
                return [Stock(
                    code=stock_data["code"],
                    name=stock_data["name"],
                    sector=stock_data["sector"],
                    market="TSE",
                    is_active=True
                ) for stock_data in StockService.POPULAR_STOCKS[:limit]]
            
            return stocks
            
        except Exception as e:
            print(f"Get popular stocks error: {str(e)}")
            # エラーの場合は静的リストから作成
            return [Stock(
                code=stock_data["code"],
                name=stock_data["name"],
                sector=stock_data["sector"],
                market="TSE",
                is_active=True
            ) for stock_data in StockService.POPULAR_STOCKS[:limit]]
    
    @staticmethod
    def get_stocks_by_sector(db: Session, sector: str, limit: int = 20) -> List[Stock]:
        """セクター別銘柄取得"""
        try:
            stocks = db.query(Stock).filter(
                Stock.sector == sector,
                Stock.is_active == True
            ).limit(limit).all()
            
            return stocks
            
        except Exception as e:
            print(f"Get stocks by sector error: {str(e)}")
            return []
    
    @staticmethod
    def get_all_sectors(db: Session) -> List[str]:
        """全セクター取得"""
        try:
            sectors = db.query(Stock.sector).distinct().all()
            return [sector[0] for sector in sectors]
            
        except Exception as e:
            print(f"Get all sectors error: {str(e)}")
            # エラーの場合は静的リストから作成
            return list(set([stock["sector"] for stock in StockService.POPULAR_STOCKS]))
    
    @staticmethod
    def initialize_stock_master_data(db: Session) -> bool:
        """株式マスタデータの初期化"""
        try:
            # 既存データの件数確認
            existing_count = db.query(Stock).count()
            
            if existing_count > 0:
                print(f"Already initialized with {existing_count} stocks")
                return True
            
            # 静的リストからデータを挿入
            for stock_data in StockService.POPULAR_STOCKS:
                existing_stock = db.query(Stock).filter(
                    Stock.code == stock_data["code"]
                ).first()
                
                if not existing_stock:
                    new_stock = Stock(
                        code=stock_data["code"],
                        name=stock_data["name"],
                        sector=stock_data["sector"],
                        market="TSE",
                        is_active=True
                    )
                    db.add(new_stock)
            
            db.commit()
            print(f"Initialized {len(StockService.POPULAR_STOCKS)} stocks")
            return True
            
        except Exception as e:
            print(f"Initialize stock master data error: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def get_stock_price_data(stock_code: str, period: str = "1M") -> StockPriceResponse:
        """株価データ取得（実際のyfinanceデータ）"""
        try:
            # 期間マッピング（テクニカル指標計算のため十分なデータを確保）
            period_mapping = {
                "1W": "90d",   # 1週間でも過去データを含めて90日分
                "1M": "90d",   # 1ヶ月で90日分
                "3M": "6mo",   # 3ヶ月で6ヶ月分
                "6M": "1y",    # 6ヶ月で1年分
                "1Y": "2y"     # 1年で2年分
            }
            
            yf_period = period_mapping.get(period, "90d")
            
            # 日本株の場合、".T"を追加
            ticker_symbol = f"{stock_code}.T"
            
            # yfinanceでデータ取得
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=yf_period)
            
            if hist.empty:
                # データが取得できない場合はフォールバック
                return StockService._get_fallback_data(stock_code, period)
            
            # DataFrameをStockPriceDataに変換
            price_data = []
            for date, row in hist.iterrows():
                price_data.append(StockPriceData(
                    time=date.strftime("%Y-%m-%d"),
                    open=round(float(row['Open']), 2),
                    high=round(float(row['High']), 2),
                    low=round(float(row['Low']), 2),
                    close=round(float(row['Close']), 2),
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else 0
                ))
            
            # 期間に応じてデータを絞り込み
            if period == "1W":
                price_data = price_data[-7:]  # 直近7日分
            elif period == "1M":
                price_data = price_data[-30:]  # 直近30日分
            elif period == "3M":
                price_data = price_data[-90:]  # 直近90日分
            elif period == "6M":
                price_data = price_data[-180:]  # 直近180日分
            elif period == "1Y":
                price_data = price_data[-365:]  # 直近365日分
            
            return StockPriceResponse(
                stock_code=stock_code,
                period=period,
                data=price_data,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            print(f"yfinance error for {stock_code}: {str(e)}")
            # エラーの場合はフォールバックデータを使用
            return StockService._get_fallback_data(stock_code, period)
    
    @staticmethod
    def _get_fallback_data(stock_code: str, period: str) -> StockPriceResponse:
        """フォールバック用のモックデータ生成"""
        # 期間マッピング
        period_mapping = {
            "1W": 7,
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365
        }
        
        days = period_mapping.get(period, 30)
        
        # 実際の株価に近いベース価格
        stock_mock_data = {
            "7203": {"base_price": 3420, "name": "トヨタ自動車"},
            "6758": {"base_price": 13850, "name": "ソニーグループ"}, 
            "9984": {"base_price": 7890, "name": "ソフトバンクG"},
            "6861": {"base_price": 52300, "name": "キーエンス"},
            "8306": {"base_price": 1200, "name": "三菱UFJフィナンシャル・グループ"},
            "4519": {"base_price": 4500, "name": "中外製薬"},
            "6098": {"base_price": 8500, "name": "リクルートホールディングス"},
            "9432": {"base_price": 3800, "name": "日本電信電話"},
            "6954": {"base_price": 28000, "name": "ファナック"},
            "8035": {"base_price": 42000, "name": "東京エレクトロン"}
        }
        
        base_price = stock_mock_data.get(stock_code, {"base_price": 1000})["base_price"]
        
        # 日付とモック価格データ生成
        price_data = []
        current_date = datetime.now() - timedelta(days=days)
        current_price = base_price
        
        import random
        for i in range(days):
            # 小さなランダム変動をシミュレート
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
    def get_stock_with_cache(db: Session, stock_code: str, period: str = "1M") -> StockPriceResponse:
        """キャッシュを使用した株価データ取得"""
        from app.services.cache_service import CacheService
        
        # キャッシュからデータを取得
        cached_data = CacheService.get_stock_price_cache(db, stock_code, period)
        if cached_data:
            return cached_data
        
        # キャッシュにない場合は新しいデータを取得
        fresh_data = StockService.get_stock_price_data(stock_code, period)
        
        # キャッシュに保存
        CacheService.set_stock_price_cache(db, stock_code, period, fresh_data)
        
        return fresh_data