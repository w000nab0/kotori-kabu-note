#!/usr/bin/env python3
"""
株式マスタデータ初期化スクリプト
日本株の主要銘柄データをデータベースに初期投入する
"""

import sys
import os
from datetime import datetime

# モジュールパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Stock
import os
from app.core.config import settings

# 拡張された日本株銘柄データ
STOCK_MASTER_DATA = [
    # 自動車・輸送機器
    {"code": "7203", "name": "トヨタ自動車", "sector": "自動車", "market": "TSE"},
    {"code": "7201", "name": "日産自動車", "sector": "自動車", "market": "TSE"},
    {"code": "7267", "name": "ホンダ", "sector": "自動車", "market": "TSE"},
    {"code": "7269", "name": "スズキ", "sector": "自動車", "market": "TSE"},
    {"code": "7270", "name": "SUBARU", "sector": "自動車", "market": "TSE"},
    {"code": "7211", "name": "三菱自動車工業", "sector": "自動車", "market": "TSE"},
    
    # 電気機器・IT
    {"code": "6758", "name": "ソニーグループ", "sector": "電気機器", "market": "TSE"},
    {"code": "6861", "name": "キーエンス", "sector": "電気機器", "market": "TSE"},
    {"code": "6954", "name": "ファナック", "sector": "電気機器", "market": "TSE"},
    {"code": "8035", "name": "東京エレクトロン", "sector": "電気機器", "market": "TSE"},
    {"code": "6752", "name": "パナソニック ホールディングス", "sector": "電気機器", "market": "TSE"},
    {"code": "6971", "name": "京セラ", "sector": "電気機器", "market": "TSE"},
    {"code": "6770", "name": "アルプスアルパイン", "sector": "電気機器", "market": "TSE"},
    {"code": "6503", "name": "三菱電機", "sector": "電気機器", "market": "TSE"},
    {"code": "6501", "name": "日立製作所", "sector": "電気機器", "market": "TSE"},
    
    # 情報・通信業
    {"code": "9984", "name": "ソフトバンクグループ", "sector": "情報・通信業", "market": "TSE"},
    {"code": "9432", "name": "日本電信電話", "sector": "情報・通信業", "market": "TSE"},
    {"code": "9433", "name": "KDDI", "sector": "情報・通信業", "market": "TSE"},
    {"code": "4689", "name": "LINEヤフー", "sector": "情報・通信業", "market": "TSE"},
    {"code": "4751", "name": "サイバーエージェント", "sector": "情報・通信業", "market": "TSE"},
    {"code": "3659", "name": "ネクソン", "sector": "情報・通信業", "market": "TSE"},
    {"code": "4755", "name": "楽天グループ", "sector": "情報・通信業", "market": "TSE"},
    
    # 金融業
    {"code": "8306", "name": "三菱UFJフィナンシャル・グループ", "sector": "銀行業", "market": "TSE"},
    {"code": "8316", "name": "三井住友フィナンシャルグループ", "sector": "銀行業", "market": "TSE"},
    {"code": "8411", "name": "みずほフィナンシャルグループ", "sector": "銀行業", "market": "TSE"},
    {"code": "8601", "name": "大和証券グループ本社", "sector": "証券業", "market": "TSE"},
    {"code": "8604", "name": "野村ホールディングス", "sector": "証券業", "market": "TSE"},
    {"code": "8725", "name": "MS&ADインシュアランスグループホールディングス", "sector": "保険業", "market": "TSE"},
    
    # 医薬品・バイオ
    {"code": "4519", "name": "中外製薬", "sector": "医薬品", "market": "TSE"},
    {"code": "4502", "name": "武田薬品工業", "sector": "医薬品", "market": "TSE"},
    {"code": "4506", "name": "住友ファーマ", "sector": "医薬品", "market": "TSE"},
    {"code": "4568", "name": "第一三共", "sector": "医薬品", "market": "TSE"},
    {"code": "4523", "name": "エーザイ", "sector": "医薬品", "market": "TSE"},
    {"code": "4503", "name": "アステラス製薬", "sector": "医薬品", "market": "TSE"},
    
    # 小売業・消費関連
    {"code": "9983", "name": "ファーストリテイリング", "sector": "小売業", "market": "TSE"},
    {"code": "3086", "name": "J.フロント リテイリング", "sector": "小売業", "market": "TSE"},
    {"code": "8267", "name": "イオン", "sector": "小売業", "market": "TSE"},
    {"code": "3382", "name": "セブン&アイ・ホールディングス", "sector": "小売業", "market": "TSE"},
    {"code": "9843", "name": "ニトリホールディングス", "sector": "小売業", "market": "TSE"},
    {"code": "2914", "name": "日本たばこ産業", "sector": "食品", "market": "TSE"},
    {"code": "2502", "name": "アサヒグループホールディングス", "sector": "食品", "market": "TSE"},
    {"code": "2503", "name": "キリンホールディングス", "sector": "食品", "market": "TSE"},
    
    # サービス業
    {"code": "6098", "name": "リクルートホールディングス", "sector": "サービス業", "market": "TSE"},
    {"code": "9202", "name": "ANA ホールディングス", "sector": "空運業", "market": "TSE"},
    {"code": "9201", "name": "日本航空", "sector": "空運業", "market": "TSE"},
    {"code": "9021", "name": "西日本旅客鉄道", "sector": "陸運業", "market": "TSE"},
    {"code": "9020", "name": "東日本旅客鉄道", "sector": "陸運業", "market": "TSE"},
    {"code": "9022", "name": "東海旅客鉄道", "sector": "陸運業", "market": "TSE"},
    
    # 素材・化学
    {"code": "6326", "name": "クボタ", "sector": "機械", "market": "TSE"},
    {"code": "6367", "name": "ダイキン工業", "sector": "機械", "market": "TSE"},
    {"code": "4063", "name": "信越化学工業", "sector": "化学", "market": "TSE"},
    {"code": "4188", "name": "三菱ケミカルグループ", "sector": "化学", "market": "TSE"},
    {"code": "4061", "name": "デンカ", "sector": "化学", "market": "TSE"},
    {"code": "5020", "name": "ENEOS ホールディングス", "sector": "石油・石炭製品", "market": "TSE"},
    {"code": "5101", "name": "横浜ゴム", "sector": "ゴム製品", "market": "TSE"},
    
    # 不動産
    {"code": "8802", "name": "三菱地所", "sector": "不動産業", "market": "TSE"},
    {"code": "8801", "name": "三井不動産", "sector": "不動産業", "market": "TSE"},
    {"code": "8830", "name": "住友不動産", "sector": "不動産業", "market": "TSE"},
    
    # 建設・建材
    {"code": "1928", "name": "積水ハウス", "sector": "建設業", "market": "TSE"},
    {"code": "1925", "name": "大和ハウス工業", "sector": "建設業", "market": "TSE"},
    {"code": "1801", "name": "大成建設", "sector": "建設業", "market": "TSE"},
    {"code": "1802", "name": "大林組", "sector": "建設業", "market": "TSE"},
    {"code": "5332", "name": "TOTO", "sector": "ガラス・土石製品", "market": "TSE"},
]

def init_stock_master_data():
    """株式マスタデータの初期化"""
    print("株式マスタデータ初期化開始...")
    
    # データベース接続
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/kotori_kabu_note")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 既存データの件数確認
        existing_count = db.query(Stock).count()
        print(f"既存データ件数: {existing_count}")
        
        # 新規データの挿入
        added_count = 0
        updated_count = 0
        
        for stock_data in STOCK_MASTER_DATA:
            # 既存データチェック
            existing_stock = db.query(Stock).filter(
                Stock.code == stock_data["code"]
            ).first()
            
            if existing_stock:
                # 既存データの更新
                existing_stock.name = stock_data["name"]
                existing_stock.sector = stock_data["sector"]
                existing_stock.market = stock_data["market"]
                existing_stock.updated_at = datetime.utcnow()
                updated_count += 1
                print(f"  更新: {stock_data['code']} - {stock_data['name']}")
            else:
                # 新規データの挿入
                new_stock = Stock(
                    code=stock_data["code"],
                    name=stock_data["name"],
                    sector=stock_data["sector"],
                    market=stock_data["market"],
                    is_active=True
                )
                db.add(new_stock)
                added_count += 1
                print(f"  追加: {stock_data['code']} - {stock_data['name']}")
        
        # コミット
        db.commit()
        
        print(f"\n✅ 株式マスタデータ初期化完了!")
        print(f"新規追加: {added_count}件")
        print(f"更新: {updated_count}件")
        print(f"総データ件数: {db.query(Stock).count()}件")
        
        # セクター別統計
        sectors = db.query(Stock.sector).distinct().all()
        print(f"\nセクター数: {len(sectors)}")
        for sector in sectors:
            sector_count = db.query(Stock).filter(Stock.sector == sector[0]).count()
            print(f"  {sector[0]}: {sector_count}件")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_stock_data():
    """株式データの検証"""
    print("\n株式データ検証開始...")
    
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/kotori_kabu_note")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 基本統計
        total_stocks = db.query(Stock).count()
        active_stocks = db.query(Stock).filter(Stock.is_active == True).count()
        
        print(f"総銘柄数: {total_stocks}")
        print(f"アクティブ銘柄数: {active_stocks}")
        
        # セクター別分布
        print("\nセクター別分布:")
        sector_stats = db.query(Stock.sector, func.count()).group_by(Stock.sector).all()
        for sector, count in sector_stats:
            print(f"  {sector}: {count}件")
        
        # 市場別分布
        print("\n市場別分布:")
        market_stats = db.query(Stock.market, func.count()).group_by(Stock.market).all()
        for market, count in market_stats:
            print(f"  {market}: {count}件")
        
        # データサンプル表示
        print("\nデータサンプル（最初の10件）:")
        sample_stocks = db.query(Stock).limit(10).all()
        for stock in sample_stocks:
            print(f"  {stock.code}: {stock.name} ({stock.sector} - {stock.market})")
        
        print("\n✅ 株式データ検証完了!")
        
    except Exception as e:
        print(f"❌ 検証エラー: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("株式マスタデータ初期化スクリプト")
    print("=" * 60)
    
    try:
        # マスタデータ初期化
        init_stock_master_data()
        
        # データ検証
        verify_stock_data()
        
        print("\n" + "=" * 60)
        print("✅ 全ての処理が完了しました!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 処理中にエラーが発生しました: {str(e)}")
        sys.exit(1)