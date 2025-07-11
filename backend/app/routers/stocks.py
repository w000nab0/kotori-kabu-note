from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.stock import (
    StockResponse, StockPriceResponse, SearchHistoryResponse, 
    BookmarkCreate, BookmarkResponse, SearchHistoryCreate, TechnicalIndicators
)
from app.services.stock_service import StockService
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.database import User, SearchHistory, Bookmark
from typing import List, Optional
from datetime import datetime

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)

@router.get("/search", response_model=List[StockResponse])
async def search_stocks(
    q: str = Query(..., description="検索クエリ（銘柄コードまたは企業名）"),
    limit: int = Query(10, description="検索結果の最大件数"),
    db: Session = Depends(get_db)
):
    """銘柄検索（オートサジェスト）"""
    try:
        stocks = StockService.search_stocks_with_db(db, q, limit)
        return [StockResponse(
            code=stock.code,
            name=stock.name,
            market=stock.market,
            sector=stock.sector,
            is_active=stock.is_active,
            updated_at=datetime.utcnow()
        ) for stock in stocks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/{stock_code}/price", response_model=StockPriceResponse)
async def get_stock_price(
    stock_code: str,
    period: str = Query("1M", description="期間: 1W, 1M, 3M, 6M, 1Y"),
    db: Session = Depends(get_db)
):
    """株価データ取得（キャッシュ機能付き）"""
    try:
        # キャッシュ付きでデータ取得
        return StockService.get_stock_with_cache(db, stock_code, period)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found: {str(e)}"
        )

@router.get("/{stock_code}/indicators", response_model=TechnicalIndicators)
async def get_technical_indicators(
    stock_code: str,
    period: str = Query("1M", description="期間: 1W, 1M, 3M, 6M, 1Y"),
    db: Session = Depends(get_db)
):
    """テクニカル指標取得"""
    try:
        # キャッシュ付きで株価データ取得
        price_data = StockService.get_stock_with_cache(db, stock_code, period)
        
        # テクニカル指標計算
        indicators = StockService.calculate_technical_indicators(price_data.data)
        
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to calculate indicators: {str(e)}"
        )

@router.post("/search-history", response_model=SearchHistoryResponse)
async def add_search_history(
    search: SearchHistoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """検索履歴追加"""
    # 重複チェック（同一銘柄の直近の検索を避ける）
    recent_search = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id,
        SearchHistory.stock_code == search.stock_code
    ).order_by(SearchHistory.searched_at.desc()).first()
    
    # 同じ銘柄の検索が10分以内にある場合はスキップ
    if recent_search:
        time_diff = datetime.utcnow() - recent_search.searched_at
        if time_diff.seconds < 600:  # 10分
            return SearchHistoryResponse(
                id=recent_search.id,
                user_id=recent_search.user_id,
                stock_code=recent_search.stock_code,
                searched_at=recent_search.searched_at
            )
    
    # 履歴数制限（100件まで）
    history_count = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).count()
    
    if history_count >= 100:
        # 最古の履歴を削除
        oldest = db.query(SearchHistory).filter(
            SearchHistory.user_id == current_user.id
        ).order_by(SearchHistory.searched_at.asc()).first()
        db.delete(oldest)
    
    # 新しい履歴追加
    new_history = SearchHistory(
        user_id=current_user.id,
        stock_code=search.stock_code
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)
    
    return SearchHistoryResponse(
        id=new_history.id,
        user_id=new_history.user_id,
        stock_code=new_history.stock_code,
        searched_at=new_history.searched_at
    )

@router.get("/search-history", response_model=List[SearchHistoryResponse])
async def get_search_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """検索履歴取得"""
    histories = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.searched_at.desc()).limit(100).all()
    
    return [SearchHistoryResponse(
        id=history.id,
        user_id=history.user_id,
        stock_code=history.stock_code,
        searched_at=history.searched_at
    ) for history in histories]

@router.post("/bookmarks", response_model=BookmarkResponse)
async def add_bookmark(
    bookmark: BookmarkCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """ブックマーク追加"""
    # 重複チェック
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.stock_code == bookmark.stock_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already bookmarked"
        )
    
    new_bookmark = Bookmark(
        user_id=current_user.id,
        stock_code=bookmark.stock_code
    )
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    
    return BookmarkResponse(
        id=new_bookmark.id,
        user_id=new_bookmark.user_id,
        stock_code=new_bookmark.stock_code,
        bookmarked_at=new_bookmark.bookmarked_at
    )

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_bookmarks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """ブックマーク一覧取得"""
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).order_by(Bookmark.bookmarked_at.desc()).all()
    
    return [BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        stock_code=bookmark.stock_code,
        bookmarked_at=bookmark.bookmarked_at
    ) for bookmark in bookmarks]

@router.delete("/bookmarks/{stock_code}")
async def remove_bookmark(
    stock_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """ブックマーク削除"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.stock_code == stock_code
    ).first()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "Bookmark removed successfully"}

@router.get("/popular", response_model=List[StockResponse])
async def get_popular_stocks(
    limit: int = Query(20, description="取得件数"),
    db: Session = Depends(get_db)
):
    """人気銘柄取得"""
    try:
        stocks = StockService.get_popular_stocks(db, limit)
        return [StockResponse(
            code=stock.code,
            name=stock.name,
            market=stock.market,
            sector=stock.sector,
            is_active=stock.is_active,
            updated_at=datetime.utcnow()
        ) for stock in stocks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular stocks: {str(e)}"
        )

@router.get("/sectors", response_model=List[str])
async def get_all_sectors(
    db: Session = Depends(get_db)
):
    """全セクター取得"""
    try:
        sectors = StockService.get_all_sectors(db)
        return sectors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sectors: {str(e)}"
        )

@router.get("/sectors/{sector}", response_model=List[StockResponse])
async def get_stocks_by_sector(
    sector: str,
    limit: int = Query(20, description="取得件数"),
    db: Session = Depends(get_db)
):
    """セクター別銘柄取得"""
    try:
        stocks = StockService.get_stocks_by_sector(db, sector, limit)
        return [StockResponse(
            code=stock.code,
            name=stock.name,
            market=stock.market,
            sector=stock.sector,
            is_active=stock.is_active,
            updated_at=datetime.utcnow()
        ) for stock in stocks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stocks by sector: {str(e)}"
        )

@router.get("/cache/stats")
async def get_cache_stats(
    db: Session = Depends(get_db)
):
    """キャッシュ統計情報取得"""
    try:
        from app.services.cache_service import CacheService
        stats = CacheService.get_cache_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )

@router.post("/cache/cleanup")
async def cleanup_cache(
    db: Session = Depends(get_db)
):
    """期限切れキャッシュのクリーンアップ"""
    try:
        from app.services.cache_service import CacheService
        deleted_count = CacheService.cleanup_expired_caches(db)
        return {"message": f"Cleaned up {deleted_count} expired cache entries"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup cache: {str(e)}"
        )

@router.post("/cache/warm-up")
async def warm_up_cache(
    db: Session = Depends(get_db)
):
    """人気銘柄のキャッシュウォームアップ"""
    try:
        from app.services.cache_service import CacheService
        popular_codes = [stock["code"] for stock in StockService.POPULAR_STOCKS[:10]]
        success = CacheService.warm_up_cache(db, popular_codes)
        return {"message": "Cache warm-up completed" if success else "Cache warm-up failed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm up cache: {str(e)}"
        )