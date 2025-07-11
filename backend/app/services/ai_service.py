import google.generativeai as genai
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import AIExplanation, DailyAPIUsage, MinuteAPIUsage, UserDailyUsage, User
from app.models.ai import AIExplanationRequest, AIExplanationResponse, APIUsageResponse
from app.models.stock import StockPriceData, TechnicalIndicators
from fastapi import HTTPException, status
import os
import json
import uuid

class AIService:
    # API制限設定
    APP_LIMITS = {
        "DAILY_REQUESTS": 170,      # 85%安全マージン (200 × 0.85)
        "MINUTE_TOKENS": 850000,    # 分間制限85% (100万 × 0.85)
        "MINUTE_REQUESTS": 25       # 分間制限85% (30 × 0.85)
    }
    TOKENS_PER_REQUEST = 650
    USER_DAILY_LIMIT = 10
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            self.enabled = False
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.enabled = True
    
    def check_api_limits(self, db: Session, user_id: uuid.UUID) -> APIUsageResponse:
        """API制限チェック"""
        today = date.today()
        current_minute = datetime.utcnow().strftime("%Y-%m-%d_%H:%M")
        
        # 1. 日次リクエスト制限チェック
        daily_usage = db.query(DailyAPIUsage).filter(
            DailyAPIUsage.usage_date == today
        ).first()
        
        daily_requests = daily_usage.total_requests if daily_usage else 0
        if daily_requests >= self.APP_LIMITS["DAILY_REQUESTS"]:
            return APIUsageResponse(
                allowed=False,
                reason="Daily request limit exceeded",
                remaining_requests=0,
                daily_limit=self.USER_DAILY_LIMIT
            )
        
        # 2. 分次リクエスト制限チェック
        minute_usage = db.query(MinuteAPIUsage).filter(
            MinuteAPIUsage.minute_key == current_minute
        ).first()
        
        minute_requests = minute_usage.requests if minute_usage else 0
        if minute_requests >= self.APP_LIMITS["MINUTE_REQUESTS"]:
            return APIUsageResponse(
                allowed=False,
                reason="Rate limit exceeded, please try again later",
                remaining_requests=0,
                daily_limit=self.USER_DAILY_LIMIT
            )
        
        # 3. 分次トークン制限チェック
        minute_tokens = minute_usage.tokens if minute_usage else 0
        if minute_tokens + self.TOKENS_PER_REQUEST > self.APP_LIMITS["MINUTE_TOKENS"]:
            return APIUsageResponse(
                allowed=False,
                reason="Token rate limit exceeded",
                remaining_requests=0,
                daily_limit=self.USER_DAILY_LIMIT
            )
        
        # 4. ユーザー日次制限チェック
        user_usage = db.query(UserDailyUsage).filter(
            UserDailyUsage.user_id == user_id,
            UserDailyUsage.usage_date == today
        ).first()
        
        user_requests = user_usage.request_count if user_usage else 0
        if user_requests >= self.USER_DAILY_LIMIT:
            return APIUsageResponse(
                allowed=False,
                reason="Daily user limit exceeded",
                remaining_requests=0,
                daily_limit=self.USER_DAILY_LIMIT
            )
        
        return APIUsageResponse(
            allowed=True,
            remaining_requests=self.USER_DAILY_LIMIT - user_requests,
            daily_limit=self.USER_DAILY_LIMIT
        )
    
    def record_usage(self, db: Session, user_id: uuid.UUID, actual_tokens: int):
        """API使用量記録"""
        today = date.today()
        current_minute = datetime.utcnow().strftime("%Y-%m-%d_%H:%M")
        
        # 日次使用量更新
        daily_usage = db.query(DailyAPIUsage).filter(
            DailyAPIUsage.usage_date == today
        ).first()
        
        if not daily_usage:
            daily_usage = DailyAPIUsage(
                usage_date=today,
                total_requests=1,
                total_tokens=actual_tokens,
                estimated_tokens=self.TOKENS_PER_REQUEST,
                actual_tokens=actual_tokens
            )
            db.add(daily_usage)
        else:
            daily_usage.total_requests += 1
            daily_usage.total_tokens += actual_tokens
            daily_usage.estimated_tokens += self.TOKENS_PER_REQUEST
            daily_usage.actual_tokens += actual_tokens
        
        # 分次使用量更新
        minute_usage = db.query(MinuteAPIUsage).filter(
            MinuteAPIUsage.minute_key == current_minute
        ).first()
        
        if not minute_usage:
            minute_usage = MinuteAPIUsage(
                minute_key=current_minute,
                requests=1,
                tokens=actual_tokens
            )
            db.add(minute_usage)
        else:
            minute_usage.requests += 1
            minute_usage.tokens += actual_tokens
        
        # ユーザー日次使用量更新
        user_usage = db.query(UserDailyUsage).filter(
            UserDailyUsage.user_id == user_id,
            UserDailyUsage.usage_date == today
        ).first()
        
        if not user_usage:
            user_usage = UserDailyUsage(
                user_id=user_id,
                usage_date=today,
                request_count=1,
                token_count=actual_tokens
            )
            db.add(user_usage)
        else:
            user_usage.request_count += 1
            user_usage.token_count += actual_tokens
        
        db.commit()
    
    def get_cached_explanation(self, db: Session, stock_code: str, period: str) -> Optional[AIExplanationResponse]:
        """キャッシュされた解説取得"""
        cached = db.query(AIExplanation).filter(
            AIExplanation.stock_code == stock_code,
            AIExplanation.chart_period == period,
            AIExplanation.expires_at > datetime.utcnow()
        ).first()
        
        if cached:
            return AIExplanationResponse(
                id=cached.id,
                stock_code=cached.stock_code,
                chart_period=cached.chart_period,
                explanation_text=cached.explanation_text,
                technical_data=cached.technical_data,
                created_at=cached.created_at,
                expires_at=cached.expires_at
            )
        return None
    
    def generate_explanation(
        self, 
        db: Session, 
        user_id: uuid.UUID,
        stock_code: str, 
        period: str,
        price_data: list[StockPriceData],
        indicators: TechnicalIndicators
    ) -> AIExplanationResponse:
        """AI解説生成"""
        
        # MVP版：Gemini APIが設定されていない場合はモック応答を返す
        if not self.enabled:
            # モック解説を生成
            mock_explanation = self._generate_mock_explanation(stock_code, price_data, indicators)
            
            # モック使用量記録
            self.record_usage(db, user_id, self.TOKENS_PER_REQUEST)
            
            # キャッシュ保存
            expires_at = datetime.utcnow() + timedelta(hours=1)
            ai_explanation = AIExplanation(
                stock_code=stock_code,
                chart_period=period,
                explanation_text=mock_explanation,
                technical_data={
                    "sma_25": indicators.sma_25,
                    "sma_75": indicators.sma_75,
                    "rsi_14": indicators.rsi_14,
                    "macd_line": indicators.macd_line,
                    "macd_signal": indicators.macd_signal,
                    "macd_histogram": indicators.macd_histogram,
                    "volume_sma_25": indicators.volume_sma_25
                },
                expires_at=expires_at
            )
            
            db.add(ai_explanation)
            db.commit()
            db.refresh(ai_explanation)
            
            return AIExplanationResponse(
                id=ai_explanation.id,
                stock_code=stock_code,
                chart_period=period,
                explanation_text=mock_explanation,
                technical_data={
                    "sma_25": indicators.sma_25,
                    "sma_75": indicators.sma_75,
                    "rsi_14": indicators.rsi_14,
                    "macd_line": indicators.macd_line,
                    "macd_signal": indicators.macd_signal,
                    "macd_histogram": indicators.macd_histogram,
                    "volume_sma_25": indicators.volume_sma_25
                },
                created_at=ai_explanation.created_at,
                expires_at=ai_explanation.expires_at
            )
        
        # キャッシュ確認
        cached = self.get_cached_explanation(db, stock_code, period)
        if cached:
            return cached
        
        # API制限チェック
        usage_check = self.check_api_limits(db, user_id)
        if not usage_check.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=usage_check.reason
            )
        
        try:
            # プロンプト作成
            prompt = self._create_prompt(stock_code, period, price_data, indicators)
            
            # Gemini API呼び出し
            response = self.model.generate_content(prompt)
            explanation_text = response.text
            
            # 使用量記録（実際のトークン数）
            actual_tokens = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else self.TOKENS_PER_REQUEST
            self.record_usage(db, user_id, actual_tokens)
            
            # キャッシュ保存
            expires_at = datetime.utcnow() + timedelta(hours=1)
            ai_explanation = AIExplanation(
                stock_code=stock_code,
                chart_period=period,
                explanation_text=explanation_text,
                technical_data={
                    "sma_25": indicators.sma_25,
                    "sma_75": indicators.sma_75,
                    "rsi_14": indicators.rsi_14,
                    "macd_line": indicators.macd_line,
                    "macd_signal": indicators.macd_signal
                },
                expires_at=expires_at
            )
            
            db.add(ai_explanation)
            db.commit()
            db.refresh(ai_explanation)
            
            return AIExplanationResponse(
                id=ai_explanation.id,
                stock_code=ai_explanation.stock_code,
                chart_period=ai_explanation.chart_period,
                explanation_text=ai_explanation.explanation_text,
                technical_data=ai_explanation.technical_data,
                created_at=ai_explanation.created_at,
                expires_at=ai_explanation.expires_at
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate AI explanation: {str(e)}"
            )
    
    def _create_prompt(self, stock_code: str, period: str, price_data: list[StockPriceData], indicators: TechnicalIndicators) -> str:
        """プロンプト作成"""
        
        # 最新の価格情報
        latest = price_data[-1] if price_data else None
        if not latest:
            return ""
        
        # 価格変化の計算
        if len(price_data) >= 2:
            prev_close = price_data[-2].close
            change_pct = ((latest.close - prev_close) / prev_close) * 100
        else:
            change_pct = 0
        
        prompt = f"""
株式コード {stock_code} の{period}チャート分析をお願いします。

【現在の状況】
- 現在価格: {latest.close:.2f}円
- 前日比: {change_pct:+.2f}%
- 出来高: {latest.volume:,}株

【テクニカル指標】
- SMA25日: {indicators.sma_25:.2f}円 (現在価格との差: {(latest.close - indicators.sma_25):.2f}円)
- SMA75日: {indicators.sma_75:.2f}円 (現在価格との差: {(latest.close - indicators.sma_75):.2f}円)
- RSI(14日): {indicators.rsi_14:.1f}
- MACD: {indicators.macd_line:.3f} (シグナル: {indicators.macd_signal:.3f})

【分析依頼】
投資初心者の女性向けに、以下の点で分析してください：
1. 現在のトレンド状況（上昇・下降・横ばい）
2. テクニカル指標から読み取れる状況
3. 初心者向けのやさしいアドバイス

【注意事項】
- 具体的な売買判断は避けてください
- やさしく分かりやすい言葉で説明してください
- 150文字以内でお願いします
- 最後に「投資判断はご自身でお決めください」を追加してください
"""
        
        return prompt
    
    def _generate_mock_explanation(
        self, 
        stock_code: str, 
        price_data: list[StockPriceData], 
        indicators: TechnicalIndicators
    ) -> str:
        """モック解説生成（MVP版）"""
        latest = price_data[-1]
        
        # 基本的な分析
        if indicators.sma_25 and indicators.sma_75:
            if indicators.sma_25 > indicators.sma_75:
                trend = "上昇トレンド"
            else:
                trend = "下降トレンド"
        else:
            trend = "横ばい"
        
        # RSIによる状況判断
        if indicators.rsi_14:
            if indicators.rsi_14 > 70:
                rsi_desc = "買われすぎ"
            elif indicators.rsi_14 < 30:
                rsi_desc = "売られすぎ"
            else:
                rsi_desc = "適正水準"
        else:
            rsi_desc = "適正水準"
        
        # MACDによるモメンタム
        if indicators.macd_histogram and indicators.macd_histogram > 0:
            momentum = "上昇の勢いがあります"
        else:
            momentum = "下降の勢いがみられます"
        
        mock_explanation = f"""
現在、{stock_code}は{trend}にあります。
RSIは{rsi_desc}の状態で、{momentum}。
短期移動平均線が長期線を上回っている場合は比較的良好な状況ですが、
投資判断はご自身でお決めください。
        """.strip()
        
        return mock_explanation