"""
データキャッシュサービス
PostgreSQLを使用したキャッシュ管理を提供
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.database import StockPriceCache, AIExplanation
from app.models.stock import StockPriceResponse
import json
import hashlib

class CacheService:
    # キャッシュ期間設定
    CACHE_DURATIONS = {
        "stock_price": timedelta(minutes=30),        # 株価データ: 30分
        "ai_explanation": timedelta(hours=4),        # AI説明: 4時間
        "popular_stocks": timedelta(hours=1),        # 人気銘柄: 1時間
        "sector_stocks": timedelta(hours=2),         # セクター別: 2時間
        "technical_indicators": timedelta(minutes=30) # テクニカル指標: 30分
    }
    
    @staticmethod
    def get_cache_key(prefix: str, **kwargs) -> str:
        """キャッシュキーの生成"""
        key_parts = [prefix]
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}={value}")
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def get_stock_price_cache(
        db: Session, 
        stock_code: str, 
        period: str
    ) -> Optional[StockPriceResponse]:
        """株価データキャッシュ取得"""
        cache_key = CacheService.get_cache_key("stock_price", code=stock_code, period=period)
        
        # キャッシュエントリ検索
        cached_entry = db.query(StockPriceCache).filter(
            and_(
                StockPriceCache.cache_key == cache_key,
                StockPriceCache.expires_at > datetime.utcnow()
            )
        ).first()
        
        if cached_entry:
            try:
                # JSON データをパース
                cache_data = json.loads(cached_entry.price_data)
                return StockPriceResponse(**cache_data)
            except Exception as e:
                print(f"Cache parse error: {str(e)}")
                # パースエラーの場合は古いキャッシュを削除
                db.delete(cached_entry)
                db.commit()
        
        return None
    
    @staticmethod
    def set_stock_price_cache(
        db: Session, 
        stock_code: str, 
        period: str,
        data: StockPriceResponse
    ) -> bool:
        """株価データキャッシュ設定"""
        try:
            cache_key = CacheService.get_cache_key("stock_price", code=stock_code, period=period)
            expires_at = datetime.utcnow() + CacheService.CACHE_DURATIONS["stock_price"]
            
            # 既存キャッシュエントリの削除
            db.query(StockPriceCache).filter(
                StockPriceCache.cache_key == cache_key
            ).delete()
            
            # 新しいキャッシュエントリ作成
            cache_entry = StockPriceCache(
                cache_key=cache_key,
                stock_code=stock_code,
                period=period,
                price_data=data.model_dump_json(),
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def get_ai_explanation_cache(
        db: Session,
        stock_code: str,
        chart_period: str
    ) -> Optional[str]:
        """AI説明キャッシュ取得"""
        cached_entry = db.query(AIExplanation).filter(
            and_(
                AIExplanation.stock_code == stock_code,
                AIExplanation.chart_period == chart_period,
                AIExplanation.expires_at > datetime.utcnow()
            )
        ).first()
        
        if cached_entry:
            return cached_entry.explanation_text
        
        return None
    
    @staticmethod
    def set_ai_explanation_cache(
        db: Session,
        stock_code: str,
        chart_period: str,
        explanation: str,
        technical_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """AI説明キャッシュ設定"""
        try:
            expires_at = datetime.utcnow() + CacheService.CACHE_DURATIONS["ai_explanation"]
            
            # 既存キャッシュエントリの削除
            db.query(AIExplanation).filter(
                and_(
                    AIExplanation.stock_code == stock_code,
                    AIExplanation.chart_period == chart_period
                )
            ).delete()
            
            # 新しいキャッシュエントリ作成
            cache_entry = AIExplanation(
                stock_code=stock_code,
                chart_period=chart_period,
                explanation_text=explanation,
                technical_data=technical_data,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"AI explanation cache set error: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def cleanup_expired_caches(db: Session) -> int:
        """期限切れキャッシュのクリーンアップ"""
        try:
            current_time = datetime.utcnow()
            
            # 期限切れ株価キャッシュを削除
            stock_price_deleted = db.query(StockPriceCache).filter(
                StockPriceCache.expires_at <= current_time
            ).delete()
            
            # 期限切れAI説明キャッシュを削除
            ai_explanation_deleted = db.query(AIExplanation).filter(
                AIExplanation.expires_at <= current_time
            ).delete()
            
            db.commit()
            
            total_deleted = stock_price_deleted + ai_explanation_deleted
            print(f"Cleaned up {total_deleted} expired cache entries")
            
            return total_deleted
            
        except Exception as e:
            print(f"Cache cleanup error: {str(e)}")
            db.rollback()
            return 0
    
    @staticmethod
    def get_cache_stats(db: Session) -> Dict[str, Any]:
        """キャッシュ統計情報の取得"""
        try:
            current_time = datetime.utcnow()
            
            # 株価キャッシュ統計
            stock_price_total = db.query(StockPriceCache).count()
            stock_price_valid = db.query(StockPriceCache).filter(
                StockPriceCache.expires_at > current_time
            ).count()
            
            # AI説明キャッシュ統計
            ai_explanation_total = db.query(AIExplanation).count()
            ai_explanation_valid = db.query(AIExplanation).filter(
                AIExplanation.expires_at > current_time
            ).count()
            
            return {
                "stock_price_cache": {
                    "total": stock_price_total,
                    "valid": stock_price_valid,
                    "expired": stock_price_total - stock_price_valid
                },
                "ai_explanation_cache": {
                    "total": ai_explanation_total,
                    "valid": ai_explanation_valid,
                    "expired": ai_explanation_total - ai_explanation_valid
                },
                "cache_hit_rate": {
                    "stock_price": stock_price_valid / max(stock_price_total, 1),
                    "ai_explanation": ai_explanation_valid / max(ai_explanation_total, 1)
                }
            }
            
        except Exception as e:
            print(f"Cache stats error: {str(e)}")
            return {}
    
    @staticmethod
    def invalidate_stock_cache(db: Session, stock_code: str) -> bool:
        """特定銘柄のキャッシュを無効化"""
        try:
            # 株価キャッシュの無効化
            stock_price_deleted = db.query(StockPriceCache).filter(
                StockPriceCache.stock_code == stock_code
            ).delete()
            
            # AI説明キャッシュの無効化
            ai_explanation_deleted = db.query(AIExplanation).filter(
                AIExplanation.stock_code == stock_code
            ).delete()
            
            db.commit()
            
            total_deleted = stock_price_deleted + ai_explanation_deleted
            print(f"Invalidated {total_deleted} cache entries for stock {stock_code}")
            
            return True
            
        except Exception as e:
            print(f"Cache invalidation error: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def warm_up_cache(db: Session, stock_codes: list[str]) -> bool:
        """キャッシュのウォームアップ"""
        try:
            from app.services.stock_service import StockService
            
            warmed_up_count = 0
            for stock_code in stock_codes:
                # 人気銘柄の株価データを事前キャッシュ
                for period in ["1W", "1M", "3M"]:
                    try:
                        # キャッシュが存在しない場合のみ取得
                        cached_data = CacheService.get_stock_price_cache(db, stock_code, period)
                        if not cached_data:
                            fresh_data = StockService.get_stock_price_data(stock_code, period)
                            CacheService.set_stock_price_cache(db, stock_code, period, fresh_data)
                            warmed_up_count += 1
                    except Exception as e:
                        print(f"Warm up error for {stock_code} {period}: {str(e)}")
            
            print(f"Warmed up {warmed_up_count} cache entries")
            return True
            
        except Exception as e:
            print(f"Cache warm up error: {str(e)}")
            return False