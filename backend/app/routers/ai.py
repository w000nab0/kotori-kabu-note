from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.ai import (
    AIExplanationRequest, AIExplanationResponse, 
    APIUsageResponse
)
from app.services.ai_service import AIService
from app.services.stock_service import StockService
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.database import User

router = APIRouter(
    prefix="/ai",
    tags=["ai"]
)

ai_service = AIService()

@router.post("/explain", response_model=AIExplanationResponse)
async def generate_ai_explanation(
    request: AIExplanationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """AIチャート解説生成"""
    try:
        # 株価データとテクニカル指標を取得
        price_data = StockService.get_stock_price_data(request.stock_code, request.chart_period)
        indicators = StockService.calculate_technical_indicators(price_data.data)
        
        # AI解説生成
        explanation = ai_service.generate_explanation(
            db=db,
            user_id=current_user.id,
            stock_code=request.stock_code,
            period=request.chart_period,
            price_data=price_data.data,
            indicators=indicators
        )
        
        return explanation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )

@router.get("/usage", response_model=APIUsageResponse)
async def check_api_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """API利用状況確認"""
    try:
        usage_info = ai_service.check_api_limits(db, current_user.id)
        return usage_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check usage: {str(e)}"
        )

@router.get("/explain/{stock_code}/{period}", response_model=AIExplanationResponse)
async def get_cached_explanation(
    stock_code: str,
    period: str,
    db: Session = Depends(get_db)
):
    """キャッシュされたAI解説取得"""
    try:
        cached = ai_service.get_cached_explanation(db, stock_code, period)
        if not cached:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cached explanation found"
            )
        return cached
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cached explanation: {str(e)}"
        )