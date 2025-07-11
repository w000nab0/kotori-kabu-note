from sqlalchemy import Column, String, Boolean, DateTime, Integer, Date, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class Bookmark(Base):
    __tablename__ = "bookmarks"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    bookmarked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('user_id', 'stock_code'),)

class AIExplanation(Base):
    __tablename__ = "ai_explanations"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_code = Column(String(10), nullable=False)
    chart_period = Column(String(20), nullable=False)
    explanation_text = Column(Text, nullable=False)
    technical_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

class Stock(Base):
    __tablename__ = "stocks"
    
    code = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    market = Column(String(20), default='TSE')
    sector = Column(String(50))
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class StockPriceCache(Base):
    __tablename__ = "stock_price_cache"
    
    stock_code = Column(String(10), primary_key=True)
    price_data = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

class DailyAPIUsage(Base):
    __tablename__ = "daily_api_usage"
    
    usage_date = Column(Date, primary_key=True)
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_tokens = Column(Integer, default=0)
    actual_tokens = Column(Integer, default=0)

class MinuteAPIUsage(Base):
    __tablename__ = "minute_api_usage"
    
    minute_key = Column(String(20), primary_key=True)
    requests = Column(Integer, default=0)
    tokens = Column(Integer, default=0)

class UserDailyUsage(Base):
    __tablename__ = "user_daily_usage"
    
    user_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    usage_date = Column(Date, primary_key=True)
    request_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)