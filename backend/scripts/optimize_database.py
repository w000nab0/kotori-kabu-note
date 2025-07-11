#!/usr/bin/env python3
"""
データベース最適化スクリプト
- インデックスの追加・最適化
- 統計情報の更新
- パフォーマンス分析
"""

import sys
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# モジュールパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.database import Base

# データベース接続設定
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/kotori_kabu_note")

def create_indexes():
    """パフォーマンス向上のためのインデックス作成"""
    print("=== インデックス作成 ===")
    
    engine = create_engine(DATABASE_URL)
    
    # 作成するインデックス定義
    indexes = [
        # 株式マスタテーブル
        ("idx_stocks_sector", "CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector) WHERE is_active = true;"),
        ("idx_stocks_name_search", "CREATE INDEX IF NOT EXISTS idx_stocks_name_search ON stocks USING gin(to_tsvector('japanese', name)) WHERE is_active = true;"),
        ("idx_stocks_updated_at", "CREATE INDEX IF NOT EXISTS idx_stocks_updated_at ON stocks(updated_at DESC);"),
        
        # 検索履歴テーブル
        ("idx_search_history_user_time", "CREATE INDEX IF NOT EXISTS idx_search_history_user_time ON search_history(user_id, searched_at DESC);"),
        ("idx_search_history_stock_code", "CREATE INDEX IF NOT EXISTS idx_search_history_stock_code ON search_history(stock_code);"),
        
        # ブックマークテーブル
        ("idx_bookmarks_user_time", "CREATE INDEX IF NOT EXISTS idx_bookmarks_user_time ON bookmarks(user_id, bookmarked_at DESC);"),
        
        # 株価キャッシュテーブル
        ("idx_cache_stock_period", "CREATE INDEX IF NOT EXISTS idx_cache_stock_period ON stock_price_cache(stock_code, period);"),
        ("idx_cache_expires_cleanup", "CREATE INDEX IF NOT EXISTS idx_cache_expires_cleanup ON stock_price_cache(expires_at) WHERE expires_at < NOW();"),
        
        # AI説明キャッシュテーブル
        ("idx_ai_explanations_stock_period", "CREATE INDEX IF NOT EXISTS idx_ai_explanations_stock_period ON ai_explanations(stock_code, chart_period);"),
        ("idx_ai_explanations_expires", "CREATE INDEX IF NOT EXISTS idx_ai_explanations_expires ON ai_explanations(expires_at);"),
        
        # API使用量テーブル
        ("idx_user_daily_usage_date", "CREATE INDEX IF NOT EXISTS idx_user_daily_usage_date ON user_daily_usage(usage_date DESC);"),
        ("idx_daily_api_usage_date", "CREATE INDEX IF NOT EXISTS idx_daily_api_usage_date ON daily_api_usage(usage_date DESC);"),
        ("idx_minute_api_usage_key", "CREATE INDEX IF NOT EXISTS idx_minute_api_usage_key ON minute_api_usage(minute_key);"),
        
        # ユーザーテーブル
        ("idx_users_last_login", "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login DESC NULLS LAST);"),
        ("idx_users_email_verified", "CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified) WHERE email_verified = true;"),
    ]
    
    with engine.connect() as conn:
        for index_name, sql in indexes:
            try:
                print(f"作成中: {index_name}")
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ {index_name}")
            except Exception as e:
                print(f"❌ {index_name}: {str(e)}")
    
    print(f"インデックス作成完了: {len(indexes)}個")

def analyze_tables():
    """テーブル統計情報の更新"""
    print("\n=== テーブル統計情報更新 ===")
    
    engine = create_engine(DATABASE_URL)
    
    # 対象テーブル
    tables = [
        "users", "stocks", "search_history", "bookmarks", 
        "stock_price_cache", "ai_explanations", 
        "daily_api_usage", "minute_api_usage", "user_daily_usage"
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                print(f"分析中: {table}")
                conn.execute(text(f"ANALYZE {table};"))
                conn.commit()
                print(f"✅ {table}")
            except Exception as e:
                print(f"❌ {table}: {str(e)}")
    
    print(f"統計情報更新完了: {len(tables)}テーブル")

def check_database_size():
    """データベースサイズとテーブルサイズの確認"""
    print("\n=== データベースサイズ確認 ===")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # データベース全体のサイズ
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
        """)
        result = cursor.fetchone()
        print(f"データベース総サイズ: {result['db_size']}")
        
        # テーブル別サイズ
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)
        
        results = cursor.fetchall()
        print("\nテーブル別サイズ:")
        print(f"{'テーブル名':<30} {'総サイズ':<15} {'テーブル':<15} {'インデックス':<15}")
        print("-" * 75)
        
        for row in results:
            print(f"{row['tablename']:<30} {row['size']:<15} {row['table_size']:<15} {row['index_size']:<15}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ サイズ確認エラー: {str(e)}")

def check_slow_queries():
    """スロークエリの確認"""
    print("\n=== スロークエリ確認 ===")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # pg_stat_statementsが利用可能かチェック
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            ) as has_pg_stat_statements;
        """)
        
        result = cursor.fetchone()
        if not result['has_pg_stat_statements']:
            print("⚠️ pg_stat_statements拡張が無効です")
            print("スロークエリ分析にはpg_stat_statements拡張が必要です")
        else:
            # 上位のスロークエリを取得
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    rows
                FROM pg_stat_statements 
                WHERE query NOT LIKE '%pg_stat_statements%'
                ORDER BY mean_exec_time DESC 
                LIMIT 10;
            """)
            
            results = cursor.fetchall()
            if results:
                print("上位スロークエリ:")
                for i, row in enumerate(results, 1):
                    print(f"\n{i}. 平均実行時間: {row['mean_exec_time']:.2f}ms")
                    print(f"   実行回数: {row['calls']}")
                    print(f"   クエリ: {row['query'][:100]}...")
            else:
                print("スロークエリデータがありません")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ スロークエリ確認エラー: {str(e)}")

def check_index_usage():
    """インデックス使用状況の確認"""
    print("\n=== インデックス使用状況確認 ===")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # インデックス使用統計
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes 
            ORDER BY idx_scan DESC, tablename;
        """)
        
        results = cursor.fetchall()
        print(f"{'テーブル':<20} {'インデックス':<30} {'スキャン回数':<12} {'読取行数':<12}")
        print("-" * 80)
        
        for row in results:
            print(f"{row['tablename']:<20} {row['indexname']:<30} {row['index_scans']:<12} {row['tuples_read']:<12}")
        
        # 未使用インデックスの確認
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname
            FROM pg_stat_user_indexes 
            WHERE idx_scan = 0
            ORDER BY tablename, indexname;
        """)
        
        unused_indexes = cursor.fetchall()
        if unused_indexes:
            print("\n未使用インデックス:")
            for row in unused_indexes:
                print(f"  - {row['tablename']}.{row['indexname']}")
        else:
            print("\n✅ 全てのインデックスが使用されています")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ インデックス使用状況確認エラー: {str(e)}")

def vacuum_analyze():
    """VACUUM ANALYZE実行"""
    print("\n=== VACUUM ANALYZE実行 ===")
    
    try:
        # autocommit=Trueでバキューム実行
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("VACUUM ANALYZE実行中...")
        cursor.execute("VACUUM ANALYZE;")
        print("✅ VACUUM ANALYZE完了")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ VACUUM ANALYZEエラー: {str(e)}")

def performance_recommendations():
    """パフォーマンス推奨事項"""
    print("\n=== パフォーマンス推奨事項 ===")
    
    recommendations = [
        "1. 定期的なVACUUM ANALYZEの実行（週次）",
        "2. 古いキャッシュデータの自動削除（日次）",
        "3. ログファイルのローテーション設定",
        "4. 検索履歴の上限設定（ユーザーあたり100件）",
        "5. 接続プールの設定（アプリケーションレベル）",
        "6. 読み取り専用レプリカの検討（高負荷時）",
        "7. パーティショニングの検討（大量データ時）",
        "8. 監視とアラートの設定（CPU、メモリ、ディスク使用量）"
    ]
    
    for rec in recommendations:
        print(rec)

def main():
    """メイン処理"""
    print("データベース最適化スクリプト実行開始")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 各最適化処理の実行
        create_indexes()
        analyze_tables()
        check_database_size()
        check_index_usage()
        check_slow_queries()
        vacuum_analyze()
        performance_recommendations()
        
        print("\n" + "=" * 60)
        print("✅ データベース最適化完了!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 最適化中にエラーが発生: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)