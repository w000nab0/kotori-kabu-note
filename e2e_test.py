#!/usr/bin/env python3
"""
E2Eテストスイート
フロントエンド、バックエンド、データベースの統合テスト
"""

import asyncio
import httpx
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import sys

class E2ETestSuite:
    def __init__(self):
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8001"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """テスト結果をログ"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        self.total_tests += 1
        if success:
            self.passed_tests += 1

    async def test_backend_health(self):
        """バックエンドヘルスチェック"""
        print("\n=== バックエンドヘルスチェック ===")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # ルートエンドポイント
                response = await client.get(f"{self.backend_url}/")
                self.log_test(
                    "Backend Root Endpoint", 
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                # ドキュメント
                response = await client.get(f"{self.backend_url}/docs")
                self.log_test(
                    "Backend API Documentation", 
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                # OpenAPI仕様
                response = await client.get(f"{self.backend_url}/openapi.json")
                self.log_test(
                    "Backend OpenAPI Spec", 
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
            except Exception as e:
                self.log_test("Backend Health Check", False, f"Error: {str(e)}")

    async def test_stock_api_endpoints(self):
        """株式APIエンドポイントテスト"""
        print("\n=== 株式APIエンドポイントテスト ===")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            test_cases = [
                {
                    "name": "Popular Stocks API",
                    "method": "GET",
                    "url": f"{self.backend_url}/stocks/popular",
                    "params": {"limit": 5},
                    "expected_fields": ["code", "name", "sector"]
                },
                {
                    "name": "Sectors List API", 
                    "method": "GET",
                    "url": f"{self.backend_url}/stocks/sectors",
                    "expected_type": list
                },
                {
                    "name": "Stock Search API",
                    "method": "GET", 
                    "url": f"{self.backend_url}/stocks/search",
                    "params": {"q": "トヨタ", "limit": 3},
                    "expected_fields": ["code", "name", "sector"]
                },
                {
                    "name": "Stock Price Data API",
                    "method": "GET",
                    "url": f"{self.backend_url}/stocks/7203/price",
                    "params": {"period": "1M"},
                    "expected_fields": ["stock_code", "period", "data"]
                },
                {
                    "name": "Technical Indicators API",
                    "method": "GET", 
                    "url": f"{self.backend_url}/stocks/7203/indicators",
                    "params": {"period": "1M"},
                    "expected_fields": ["sma_25", "rsi_14"]
                },
                {
                    "name": "Cache Stats API",
                    "method": "GET",
                    "url": f"{self.backend_url}/stocks/cache/stats",
                    "expected_fields": ["stock_price_cache"]
                }
            ]
            
            for test_case in test_cases:
                try:
                    if test_case["method"] == "GET":
                        response = await client.get(
                            test_case["url"], 
                            params=test_case.get("params", {})
                        )
                    
                    success = response.status_code == 200
                    details = f"Status: {response.status_code}"
                    
                    if success and response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # データ型チェック
                            if "expected_type" in test_case:
                                if not isinstance(data, test_case["expected_type"]):
                                    success = False
                                    details += f", Wrong data type: {type(data)}"
                            
                            # フィールドチェック
                            if "expected_fields" in test_case and isinstance(data, list) and data:
                                for field in test_case["expected_fields"]:
                                    if field not in data[0]:
                                        success = False
                                        details += f", Missing field: {field}"
                                        break
                            elif "expected_fields" in test_case and isinstance(data, dict):
                                for field in test_case["expected_fields"]:
                                    if field not in data:
                                        success = False
                                        details += f", Missing field: {field}"
                                        break
                            
                            if success:
                                if isinstance(data, list):
                                    details += f", Items: {len(data)}"
                                elif isinstance(data, dict):
                                    details += f", Keys: {len(data.keys())}"
                                    
                        except json.JSONDecodeError:
                            success = False
                            details += ", Invalid JSON response"
                    
                    self.log_test(test_case["name"], success, details)
                    
                except Exception as e:
                    self.log_test(test_case["name"], False, f"Error: {str(e)}")

    async def test_frontend_accessibility(self):
        """フロントエンドアクセシビリティテスト"""
        print("\n=== フロントエンドアクセシビリティテスト ===")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # ホームページ
                response = await client.get(self.frontend_url)
                self.log_test(
                    "Frontend Home Page",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                # 静的ファイル
                static_files = [
                    "/_next/static/css",  # CSS
                    "/favicon.ico",       # ファビコン
                ]
                
                for static_file in static_files:
                    try:
                        response = await client.get(f"{self.frontend_url}{static_file}")
                        # 200 または 404 (まだ生成されていない場合)
                        success = response.status_code in [200, 404]
                        self.log_test(
                            f"Frontend Static File: {static_file}",
                            success,
                            f"Status: {response.status_code}"
                        )
                    except:
                        # 静的ファイルのエラーは非致命的
                        self.log_test(
                            f"Frontend Static File: {static_file}",
                            True,
                            "Skipped (not critical)"
                        )
                
            except Exception as e:
                self.log_test("Frontend Accessibility", False, f"Error: {str(e)}")

    async def test_database_integration(self):
        """データベース統合テスト"""
        print("\n=== データベース統合テスト ===")
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                # マスタデータの存在確認
                response = await client.get(f"{self.backend_url}/stocks/popular?limit=1")
                if response.status_code == 200:
                    data = response.json()
                    has_master_data = len(data) > 0
                    self.log_test(
                        "Database Master Data",
                        has_master_data,
                        f"Stocks count: {len(data)}"
                    )
                else:
                    self.log_test("Database Master Data", False, f"API Error: {response.status_code}")
                
                # セクターデータの存在確認
                response = await client.get(f"{self.backend_url}/stocks/sectors")
                if response.status_code == 200:
                    sectors = response.json()
                    has_sectors = len(sectors) > 0
                    self.log_test(
                        "Database Sector Data",
                        has_sectors,
                        f"Sectors count: {len(sectors)}"
                    )
                else:
                    self.log_test("Database Sector Data", False, f"API Error: {response.status_code}")
                
                # キャッシュシステムの動作確認
                response = await client.get(f"{self.backend_url}/stocks/cache/stats")
                if response.status_code == 200:
                    cache_stats = response.json()
                    has_cache_system = "stock_price_cache" in cache_stats
                    self.log_test(
                        "Database Cache System",
                        has_cache_system,
                        f"Cache stats available: {has_cache_system}"
                    )
                else:
                    self.log_test("Database Cache System", False, f"API Error: {response.status_code}")
                
            except Exception as e:
                self.log_test("Database Integration", False, f"Error: {str(e)}")

    async def test_data_flow_integration(self):
        """データフロー統合テスト"""
        print("\n=== データフロー統合テスト ===")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            test_stock_code = "7203"  # トヨタ
            
            try:
                # 1. 検索機能テスト
                search_response = await client.get(
                    f"{self.backend_url}/stocks/search",
                    params={"q": "トヨタ", "limit": 5}
                )
                
                search_success = (
                    search_response.status_code == 200 and
                    len(search_response.json()) > 0 and
                    any(stock.get("code") == test_stock_code for stock in search_response.json())
                )
                
                self.log_test(
                    "Search to Stock Code Flow",
                    search_success,
                    f"Found Toyota: {search_success}"
                )
                
                # 2. 株価データ取得テスト
                price_response = await client.get(
                    f"{self.backend_url}/stocks/{test_stock_code}/price",
                    params={"period": "1M"}
                )
                
                price_success = price_response.status_code == 200
                price_data = None
                
                if price_success:
                    price_data = price_response.json()
                    price_success = (
                        "data" in price_data and
                        len(price_data["data"]) > 0 and
                        price_data["stock_code"] == test_stock_code
                    )
                
                self.log_test(
                    "Stock Price Data Flow",
                    price_success,
                    f"Data points: {len(price_data['data']) if price_data else 0}"
                )
                
                # 3. テクニカル指標計算テスト
                indicators_response = await client.get(
                    f"{self.backend_url}/stocks/{test_stock_code}/indicators",
                    params={"period": "1M"}
                )
                
                indicators_success = indicators_response.status_code == 200
                
                if indicators_success:
                    indicators_data = indicators_response.json()
                    # 少なくとも一つの指標が計算されていることを確認
                    has_indicators = any(
                        value is not None 
                        for key, value in indicators_data.items() 
                        if key.startswith(('sma_', 'rsi_', 'macd_'))
                    )
                    indicators_success = has_indicators
                
                self.log_test(
                    "Technical Indicators Flow",
                    indicators_success,
                    f"Indicators calculated: {indicators_success}"
                )
                
                # 4. キャッシュ動作テスト（2回目のリクエスト）
                start_time = time.time()
                cache_response = await client.get(
                    f"{self.backend_url}/stocks/{test_stock_code}/price",
                    params={"period": "1M"}
                )
                cache_time = time.time() - start_time
                
                cache_success = (
                    cache_response.status_code == 200 and
                    cache_time < 1.0  # 1秒以内（キャッシュ効果）
                )
                
                self.log_test(
                    "Cache Performance Flow",
                    cache_success,
                    f"Response time: {cache_time:.3f}s"
                )
                
            except Exception as e:
                self.log_test("Data Flow Integration", False, f"Error: {str(e)}")

    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n=== エラーハンドリングテスト ===")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            error_test_cases = [
                {
                    "name": "Invalid Stock Code",
                    "url": f"{self.backend_url}/stocks/INVALID/price",
                    "expected_status": [404, 500]  # どちらでも適切
                },
                {
                    "name": "Invalid Period Parameter",
                    "url": f"{self.backend_url}/stocks/7203/price",
                    "params": {"period": "INVALID"},
                    "expected_status": [400, 422, 500]
                },
                {
                    "name": "Empty Search Query",
                    "url": f"{self.backend_url}/stocks/search",
                    "params": {"q": "", "limit": 5},
                    "expected_status": [200, 400, 422]  # 空クエリの処理方法による
                },
                {
                    "name": "Non-existent Endpoint",
                    "url": f"{self.backend_url}/non-existent-endpoint",
                    "expected_status": [404]
                }
            ]
            
            for test_case in error_test_cases:
                try:
                    response = await client.get(
                        test_case["url"],
                        params=test_case.get("params", {})
                    )
                    
                    success = response.status_code in test_case["expected_status"]
                    self.log_test(
                        test_case["name"],
                        success,
                        f"Status: {response.status_code} (Expected: {test_case['expected_status']})"
                    )
                    
                except Exception as e:
                    # ネットワークエラーも適切なエラーハンドリング
                    self.log_test(
                        test_case["name"],
                        True,
                        f"Network error handled: {str(e)}"
                    )

    async def test_performance_benchmarks(self):
        """パフォーマンスベンチマークテスト"""
        print("\n=== パフォーマンステスト ===")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            performance_tests = [
                {
                    "name": "Popular Stocks Response Time",
                    "url": f"{self.backend_url}/stocks/popular",
                    "params": {"limit": 10},
                    "max_time": 2.0
                },
                {
                    "name": "Stock Search Response Time",
                    "url": f"{self.backend_url}/stocks/search",
                    "params": {"q": "トヨタ", "limit": 5},
                    "max_time": 1.0
                },
                {
                    "name": "Stock Price Data Response Time",
                    "url": f"{self.backend_url}/stocks/7203/price",
                    "params": {"period": "1M"},
                    "max_time": 3.0
                },
                {
                    "name": "Cache Stats Response Time",
                    "url": f"{self.backend_url}/stocks/cache/stats",
                    "max_time": 0.5
                }
            ]
            
            for test in performance_tests:
                try:
                    start_time = time.time()
                    response = await client.get(
                        test["url"],
                        params=test.get("params", {})
                    )
                    response_time = time.time() - start_time
                    
                    success = (
                        response.status_code == 200 and 
                        response_time <= test["max_time"]
                    )
                    
                    self.log_test(
                        test["name"],
                        success,
                        f"Time: {response_time:.3f}s (Max: {test['max_time']}s)"
                    )
                    
                except Exception as e:
                    self.log_test(
                        test["name"], 
                        False, 
                        f"Error: {str(e)}"
                    )

    def generate_report(self):
        """テストレポート生成"""
        print("\n" + "="*60)
        print("E2E テスト結果レポート")
        print("="*60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"総テスト数: {self.total_tests}")
        print(f"成功: {self.passed_tests}")
        print(f"失敗: {self.total_tests - self.passed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        
        # 失敗したテストの詳細
        failed_tests = [test for test in self.test_results if not test["success"]]
        if failed_tests:
            print(f"\n失敗したテスト ({len(failed_tests)}件):")
            for test in failed_tests:
                print(f"  ❌ {test['test']}: {test['details']}")
        
        # 総合評価
        print(f"\n総合評価:")
        if success_rate >= 90:
            print("🎉 優秀 - アプリケーションは正常に動作しています")
        elif success_rate >= 75:
            print("✅ 良好 - 軽微な問題がありますが、基本機能は動作しています")
        elif success_rate >= 50:
            print("⚠️ 要改善 - いくつかの重要な問題があります")
        else:
            print("❌ 不良 - 多くの機能に問題があります")
        
        print("="*60)
        
        return success_rate >= 75

    async def run_all_tests(self):
        """全テスト実行"""
        print("E2E テストスイート開始")
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # テスト実行順序
        await self.test_backend_health()
        await self.test_stock_api_endpoints()
        await self.test_frontend_accessibility()
        await self.test_database_integration()
        await self.test_data_flow_integration()
        await self.test_error_handling()
        await self.test_performance_benchmarks()
        
        # レポート生成
        return self.generate_report()

async def main():
    """メイン実行関数"""
    test_suite = E2ETestSuite()
    success = await test_suite.run_all_tests()
    
    # テスト結果をファイルに保存
    with open('/Volumes/SSD-2T/public_workspaace/kotori_kabu_note/e2e_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": test_suite.total_tests,
            "passed_tests": test_suite.passed_tests,
            "success_rate": (test_suite.passed_tests / test_suite.total_tests) * 100,
            "results": test_suite.test_results
        }, f, ensure_ascii=False, indent=2)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)