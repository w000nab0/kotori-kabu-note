from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid

class StockBase(BaseModel):
    code: str
    name: str
    market: str = "TSE"
    sector: Optional[str] = None

class StockCreate(StockBase):
    pass

class StockResponse(StockBase):
    is_active: bool
    updated_at: datetime

    class Config:
        from_attributes = True

class StockPriceData(BaseModel):
    time: str  # ISO format timestamp
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None

class StockPriceResponse(BaseModel):
    stock_code: str
    period: str
    data: List[StockPriceData]
    last_updated: datetime

class TechnicalIndicators(BaseModel):
    sma_25: Optional[float] = None
    sma_75: Optional[float] = None
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    volume_sma_25: Optional[float] = None

class SearchHistoryCreate(BaseModel):
    stock_code: str

class SearchHistoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    stock_code: str
    searched_at: datetime

    class Config:
        from_attributes = True

class BookmarkCreate(BaseModel):
    stock_code: str

class BookmarkResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    stock_code: str
    bookmarked_at: datetime

    class Config:
        from_attributes = True