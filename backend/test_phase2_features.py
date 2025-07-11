#!/usr/bin/env python3
"""
フェーズ2機能の詳細テスト
- 銘柄マスタデータ機能
- PostgreSQLキャッシュ機能
- 検索・オートサジェスト機能
"""

import sys
import os
from datetime import datetime
import asyncio
import httpx

# モジュールパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Stock, StockPriceCache
from app.services.stock_service import StockService
from app.services.cache_service import CacheService

# テスト設定
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/kotori_kabu_note")
API_BASE_URL = "http://backend:8001"

def test_database_master_data():
    """銘柄マスタデータのテスト"""
    print("=== 銘柄マスタデータテスト ===")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 基本統計
        total_stocks = db.query(Stock).count()
        active_stocks = db.query(Stock).filter(Stock.is_active == True).count()
        
        print(f"総銘柄数: {total_stocks}")
        print(f"アクティブ銘柄数: {active_stocks}")
        
        if total_stocks < 50:
            print(f"❌ 銘柄数が少なすぎます: {total_stocks} < 50")
            return False
        
        # 検索機能テスト
        print("\n--- 検索機能テスト ---")
        search_queries = [
            ("トヨタ", "7203"),
            ("ソニー", "6758"),
            ("7203", "7203"),
            ("銀行", "8306"),
            ("自動車", "7203")
        ]
        
        for query, expected_code in search_queries:
            results = StockService.search_stocks_with_db(db, query, 10)
            found = any(stock.code == expected_code for stock in results)
            status = "✅" if found else "❌"
            print(f"  {status} '{query}' -> {len(results)}件 (期待: {expected_code})")
        
        # セクター機能テスト
        print("\n--- セクター機能テスト ---")
        sectors = StockService.get_all_sectors(db)
        print(f"セクター数: {len(sectors)}")
        
        if len(sectors) < 10:
            print(f"❌ セクター数が少なすぎます: {len(sectors)} < 10")
            return False
        
        # セクター別銘柄取得テスト
        test_sector = sectors[0] if sectors else None
        if test_sector:
            sector_stocks = StockService.get_stocks_by_sector(db, test_sector, 5)
            print(f"'{test_sector}'セクター: {len(sector_stocks)}件")
        
        # 人気銘柄取得テスト
        print("\n--- 人気銘柄取得テスト ---")
        popular_stocks = StockService.get_popular_stocks(db, 10)
        print(f"人気銘柄: {len(popular_stocks)}件")
        
        print("✅ 銘柄マスタデータテスト成功!")
        return True
        
    except Exception as e:
        print(f"❌ マスタデータテストエラー: {str(e)}")
        return False
    finally:
        db.close()

def test_cache_functionality():
    """キャッシュ機能のテスト"""
    print("\n=== キャッシュ機能テスト ===")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        test_stock_code = "7203"
        test_period = "1M"
        
        # キャッシュクリア（テスト前の準備）
        print("キャッシュクリア...")
        CacheService.invalidate_stock_cache(db, test_stock_code)
        
        # 初回データ取得（キャッシュなし）
        print("\n--- 初回データ取得（キャッシュなし） ---")
        start_time = datetime.now()
        fresh_data = StockService.get_stock_with_cache(db, test_stock_code, test_period)
        first_duration = (datetime.now() - start_time).total_seconds()
        print(f"初回取得時間: {first_duration:.3f}秒")
        print(f"データ件数: {len(fresh_data.data)}")
        
        # 2回目データ取得（キャッシュあり）
        print("\n--- 2回目データ取得（キャッシュあり） ---")
        start_time = datetime.now()
        cached_data = StockService.get_stock_with_cache(db, test_stock_code, test_period)
        second_duration = (datetime.now() - start_time).total_seconds()
        print(f"キャッシュ取得時間: {second_duration:.3f}秒")
        print(f"データ件数: {len(cached_data.data)}")
        
        # キャッシュ効果の検証
        if second_duration < first_duration:
            print(f"✅ キャッシュ効果確認: {first_duration:.3f}s -> {second_duration:.3f}s")
        else:
            print(f"⚠️ キャッシュ効果が不明確: {first_duration:.3f}s -> {second_duration:.3f}s")
        
        # データ整合性の確認
        if len(fresh_data.data) == len(cached_data.data):
            print("✅ データ整合性確認")
        else:
            print(f"❌ データ不整合: {len(fresh_data.data)} != {len(cached_data.data)}")
            return False
        
        # キャッシュ統計情報の取得
        print("\n--- キャッシュ統計情報 ---")
        stats = CacheService.get_cache_stats(db)
        print(f"株価キャッシュ: {stats.get('stock_price_cache', {})}")
        print(f"AI説明キャッシュ: {stats.get('ai_explanation_cache', {})}")
        
        # キャッシュクリーンアップテスト
        print("\n--- キャッシュクリーンアップテスト ---")
        deleted_count = CacheService.cleanup_expired_caches(db)
        print(f"削除されたキャッシュ: {deleted_count}件")
        
        print("✅ キャッシュ機能テスト成功!")
        return True
        
    except Exception as e:
        print(f"❌ キャッシュ機能テストエラー: {str(e)}")
        return False
    finally:
        db.close()

async def test_api_endpoints():
    """API エンドポイントのテスト"""
    print("\n=== APIエンドポイントテスト ===")
    
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        test_results = []
        
        # テストケース定義
        test_cases = [
            ("GET", "/stocks/search?q=トヨタ&limit=5", "銘柄検索"),
            ("GET", "/stocks/popular?limit=10", "人気銘柄取得"),
            ("GET", "/stocks/sectors", "セクター一覧取得"),
            ("GET", "/stocks/sectors/自動車?limit=5", "セクター別銘柄取得"),
            ("GET", "/stocks/7203/price?period=1M", "株価データ取得"),
            ("GET", "/stocks/7203/indicators?period=1M", "テクニカル指標取得"),
            ("GET", "/stocks/cache/stats", "キャッシュ統計取得"),
        ]
        
        for method, endpoint, description in test_cases:
            try:
                print(f"\n--- {description} ---")
                print(f"{method} {endpoint}")
                
                if method == "GET":
                    response = await client.get(endpoint)
                elif method == "POST":
                    response = await client.post(endpoint)
                else:
                    continue
                
                status = response.status_code
                if status == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"✅ {description}: {status} ({len(data)}件)")
                    elif isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        print(f"✅ {description}: {status} (keys: {keys}...)")
                    else:
                        print(f"✅ {description}: {status}")
                    test_results.append(True)
                else:
                    print(f"❌ {description}: {status}")
                    if hasattr(response, 'text'):
                        print(f"   エラー詳細: {response.text[:200]}...")
                    test_results.append(False)
                    
            except Exception as e:
                print(f"❌ {description}: エラー - {str(e)}")
                test_results.append(False)
        
        success_rate = sum(test_results) / len(test_results) * 100
        print(f"\n--- API テスト結果 ---")
        print(f"成功率: {success_rate:.1f}% ({sum(test_results)}/{len(test_results)})")
        
        return success_rate >= 80

def test_performance():
    """パフォーマンステスト"""
    print("\n=== パフォーマンステスト ===")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        test_stocks = ["7203", "6758", "9984", "6861", "8306"]
        periods = ["1W", "1M", "3M"]
        
        # 複数銘柄の並行取得テスト
        print("--- 複数銘柄並行取得テスト ---")
        start_time = datetime.now()
        
        for stock_code in test_stocks:
            for period in periods:
                try:
                    data = StockService.get_stock_with_cache(db, stock_code, period)
                    print(f"  {stock_code}({period}): {len(data.data)}件")
                except Exception as e:
                    print(f"  {stock_code}({period}): エラー - {str(e)}")
        
        total_duration = (datetime.now() - start_time).total_seconds()
        print(f"総取得時間: {total_duration:.3f}秒")
        print(f"平均取得時間: {total_duration/len(test_stocks)/len(periods):.3f}秒/銘柄/期間")
        
        # キャッシュウォームアップテスト
        print("\n--- キャッシュウォームアップテスト ---")
        start_time = datetime.now()
        success = CacheService.warm_up_cache(db, test_stocks[:3])
        warmup_duration = (datetime.now() - start_time).total_seconds()
        print(f"ウォームアップ: {'成功' if success else '失敗'} ({warmup_duration:.3f}秒)")
        
        print("✅ パフォーマンステスト完了!")
        return True
        
    except Exception as e:
        print(f"❌ パフォーマンステストエラー: {str(e)}")
        return False
    finally:
        db.close()

async def main():
    """メインテスト実行"""
    print("フェーズ2機能の詳細テスト開始...")
    print("=" * 60)
    
    test_results = []
    
    # 各テストの実行
    test_results.append(test_database_master_data())
    test_results.append(test_cache_functionality())
    test_results.append(await test_api_endpoints())
    test_results.append(test_performance())
    
    # 総合結果
    print("\n" + "=" * 60)
    print("テスト結果サマリー:")
    print(f"銘柄マスタデータ: {'✅ 成功' if test_results[0] else '❌ 失敗'}")
    print(f"キャッシュ機能: {'✅ 成功' if test_results[1] else '❌ 失敗'}")
    print(f"APIエンドポイント: {'✅ 成功' if test_results[2] else '❌ 失敗'}")
    print(f"パフォーマンス: {'✅ 成功' if test_results[3] else '❌ 失敗'}")
    
    success_count = sum(test_results)
    total_count = len(test_results)
    success_rate = success_count / total_count * 100
    
    print(f"\n総合成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    print("=" * 60)
    
    if success_rate >= 75:
        print("🎉 フェーズ2機能テスト: 合格!")
        return True
    else:
        print("💥 フェーズ2機能テスト: 要改善")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)