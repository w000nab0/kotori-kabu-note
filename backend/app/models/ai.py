from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class AIExplanationRequest(BaseModel):
    stock_code: str
    chart_period: str  # "1W", "1M", "3M", "6M", "1Y"

class AIExplanationResponse(BaseModel):
    id: uuid.UUID
    stock_code: str
    chart_period: str
    explanation_text: str
    technical_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class APIUsageRequest(BaseModel):
    user_id: uuid.UUID
    estimated_tokens: int = 650  # デフォルトトークン数

class APIUsageResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    remaining_requests: int
    daily_limit: int

class DailyAPIUsage(BaseModel):
    usage_date: datetime
    total_requests: int
    total_tokens: int
    estimated_tokens: int
    actual_tokens: int

class UserDailyUsage(BaseModel):
    user_id: uuid.UUID
    usage_date: datetime
    request_count: int
    token_count: int