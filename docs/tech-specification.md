# 📋 コトリの株ノート 最終技術仕様書

## 🎯 技術スタック（安定重視版）

### フロントエンド
- **フレームワーク**: Next.js 15 + React 18
- **UIライブラリ**: Tailwind CSS v3 + shadcn/ui
- **チャートライブラリ**: TradingView Lightweight Charts
- **アナリティクス**: Google Analytics 4
- **パッケージマネージャー**: pnpm（推奨）

### バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI 0.115+
- **データ取得**: yfinance 0.2.51+
- **AI**: Google Gemini 2.0 Flash-Lite API

### データベース・インフラ
- **データベース**: Supabase PostgreSQL
- **フロントエンドデプロイ**: Vercel
- **バックエンドデプロイ**: Render
- **環境変数管理**: Vercel + Render 環境変数機能

### 必要な環境変数
```
# API Keys
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# JWT
JWT_SECRET=your_jwt_secret_key
REFRESH_TOKEN_SECRET=your_refresh_token_secret

# External APIs
YFINANCE_TIMEOUT=30

# Monitoring
SENTRY_DSN=your_sentry_dsn_url
GA_TRACKING_ID=your_google_analytics_id

# App Configuration
NEXT_PUBLIC_API_URL=your_backend_api_url
CORS_ORIGIN=your_frontend_url
```

## 🔧 運用設計

### データ更新・容量管理
- **更新頻度**: 30分毎（無料枠制限内）
- **Supabase無料枠**: 500MB DB、月2GB帯域幅（データベース専用）
- **対象市場**: 日本株のみ
- **データ精度**: 15-20分遅延（yfinance）

### ユーザーデータ管理
- **会員登録必須**: メールアドレス + パスワード認証
- **ユーザー認証**: JWT トークンベース
- **セッション管理**: Access Token 1時間 + Refresh Token 7日間
- **検索履歴**: データベース保存、100件まで
- **AI解説**: 1日10回まで
- **データ保護**: メールアドレスのみ保存、最小限の個人情報

### 監視・バックアップ
- **エラー監視**: Sentry（10,000エラー/月無料）
- **アクセス分析**: Google Analytics 4
- **API監視**: Gemini APIクォータ使用率監視（制限超過防止）
- **データ監視**: yfinance API応答時間・失敗率監視
- **DB監視**: Supabase内蔵ダッシュボード
- **バックアップ**: Supabase自動バックアップ + 週1回手動確認

## 🎨 デザイン・UI仕様

### デザインシステム
- **カラーパレット**: パステルカラー・グレージュ系
- **レスポンシブ**: スマホファースト
- **ボタンサイズ**: 48px以上（タップしやすさ重視）
- **アニメーション**: フェードイン、スライド

### AI機能
- **API**: Google Gemini 2.0 Flash-Lite
- **生成方式**: オンデマンド生成（事前生成なし）
- **キャッシュ**: 1時間保持（サーバーサイド）
- **制限管理**: トークンベース精密制限（無料枠内運用）
- **ユーザー制限**: 1日10回まで
- **プロンプト設計**: 投資初心者向け、やさしい文体
- **コメント例**: 「最近は横ばいですね。焦らず見守りましょう。」
- **免責事項**: 自動添付「投資判断はご自身で」

## 🔒 法的対応

### 免責事項
```
当サービスは投資助言・勧誘を目的としたものではありません。
投資判断は必ずご自身の責任において行ってください。
当サービスの情報による投資結果について、一切の責任を負いません。
```

### 利用規約
```
本サービスの利用には同意が必要です。
データの正確性は保証されません。
サービスの継続性は保証されません。
```

## 🚀 開発環境

### 開発ツール
- **OS**: macOS + Docker環境
- **エディタ**: Cursor
- **バージョン管理**: Git + GitHub
- **CI/CD**: GitHub Actions（Vercel/Render連携）

### 開発フロー
```
1. ローカル開発（Docker）
2. GitHub push
3. 自動デプロイ
   - Vercel（フロントエンド）
   - Render（バックエンド）
   - Supabase（データベース）
```

## 📊 スケーリング戦略

### 段階的移行計画
1. **Phase 1**: 無料枠内運用
2. **Phase 2**: 有料プラン移行（ユーザー増加時）
3. **Phase 3**: 専用インスタンス（大規模運用）

### パフォーマンス最適化
- **CDN**: Vercel自動CDN配信
- **画像最適化**: WebP/AVIF自動変換
- **キャッシュ**: 株価データ30分、AI解説1時間
- **レスポンス時間**: 2秒以内目標

## 🤖 AI解説管理（Gemini 2.0 Flash-Lite）

### API制限管理システム
- **API**: Gemini 2.0 Flash-Lite
- **無料枠制限**: 
  - RPD: 200リクエスト/日
  - RPM: 30リクエスト/分
  - TPM: 1,000,000トークン/分
  - Context Caching: 100万トークン/時間
- **安全マージン**: 85%（RPD: 170リクエスト、RPM: 25リクエスト）
- **1回のトークン使用**: 約650トークン（入力500 + 出力150）
- **ユーザー制限**: 1日10回まで（想定同時ユーザー: 約17名まで安全運用）

### 精密制限チェックシステム
```javascript
class PreciseAPILimitManager {
  constructor() {
    this.APP_LIMITS = {
      DAILY_REQUESTS: 170,      // 85%安全マージン (200 × 0.85)
      MINUTE_TOKENS: 850000,    // 分間制限85% (100万 × 0.85)
      MINUTE_REQUESTS: 25       // 分間制限85% (30 × 0.85)
    };
    this.TOKENS_PER_REQUEST = 650;
    this.USER_DAILY_LIMIT = 10;
  }

  async checkAllLimits(userId) {
    // 1. 日次リクエスト制限チェック (RPD: 170)
    // 2. 分次リクエスト制限チェック (RPM: 25)
    // 3. 分次トークン制限チェック (TPM: 850,000)
    // 4. ユーザー日次制限チェック (10回/日)
    // 5. 実際のトークン使用量記録
    return { allowed: boolean, reason?: string };
  }
}
```

### トークン使用量追跡
```javascript
// Gemini 2.0 Flash-Lite APIレスポンスから実際のトークン数取得
const response = await gemini.generateContent(prompt);
const tokensUsed = response.usageMetadata.totalTokenCount;
await limitManager.recordUsage(userId, tokensUsed);
```


### 容量最適化
- **解説文制限**: 150文字以内
- **トークン予測**: 650トークン/回
- **制限管理**: RPD(170), RPM(25), TPM(850,000)の3重チェック
- **ユーザー拡張**: 17名→100名規模への拡張時は有料tier移行検討
- **ログ削除**: 6ヶ月以上古いデータ自動削除
- **コスト管理**: 無料枠内で確実に運用

## 📅 開発スケジュール

### 開発期間: 約3-4週間（MVP版）

#### フェーズ1: 環境構築・基盤設計 (1週間)
1. Docker環境セットアップ
2. Next.js 15 + shadcn/ui プロジェクト初期化
3. Supabase PostgreSQL データベース設計・構築
4. FastAPI + yfinance バックエンド基盤構築
5. GitHub リポジトリ作成・CI/CD設定
6. ユーザー認証システム設計・実装
7. **API制限管理システム実装**（重要機能）

#### フェーズ2: データ機能実装 (1週間)
1. 株価データ取得API（yfinance）実装・テスト
2. 銘柄マスタデータ構築・更新機能
3. PostgreSQL データキャッシュ機能実装
4. 銘柄検索・オートサジェスト機能実装

#### フェーズ3: UI・チャート機能実装 (1週間)
1. Lightweight Charts チャート表示実装
2. 期間切替・テクニカル指標表示機能
3. パステルカラー・グレージュ系デザイン適用
4. スマホ対応レスポンシブUI実装
5. 検索履歴機能（データベース保存）

#### フェーズ4: AI機能・運用準備 (1週間)
1. Gemini 2.0 Flash-Lite API 連携実装
2. 投資初心者向けチャート解説生成・テスト
3. API制限管理システム統合・テスト（Phase1で実装済み）
4. 監視・ログ設定（Sentry等）
5. 免責事項・利用規約実装
6. 30分毎データ更新バッチ設定
7. デプロイ・統合テスト・最適化

---

## 🎯 技術仕様まとめ

### MVP版テクニカル指標
```
✅ 確定仕様:
- SMA: 25日・75日
- RSI: 14日設定
- MACD: デフォルト設定
- 出来高: 25日平均と比較
```

### 登録ユーザー機能
```
✅ 機能利用制限:
- 銘柄検索: 無制限
- AI解説: 1日10回まで
- 検索履歴: 100件まで（データベース保存）
- チャート表示: 1年分データ
- 全テクニカル指標利用可能
```

### データ管理
```
✅ 更新頻度:
- 株価データ: 30分毎
- 銘柄DB: 月1回（yfinanceエラーチェック）
- AI解説: オンデマンド生成、1時間キャッシュ
```

---

## 📊 データベース設計（更新版）

```sql
-- ユーザー管理テーブル
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    CREATE INDEX idx_email ON users (email);
);

-- 検索履歴テーブル（100件制限）
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stock_code VARCHAR(10) NOT NULL,
    searched_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_user_history_limit CHECK (
        (SELECT COUNT(*) FROM search_history sh WHERE sh.user_id = search_history.user_id) <= 100
    )
);
CREATE INDEX idx_user_searched ON search_history (user_id, searched_at DESC);

-- ブックマークテーブル
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stock_code VARCHAR(10) NOT NULL,
    bookmarked_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, stock_code)
);
CREATE INDEX idx_user_bookmarks ON bookmarks (user_id, bookmarked_at DESC);

-- AI解説キャッシュテーブル
CREATE TABLE ai_explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_code VARCHAR(10) NOT NULL,
    chart_period VARCHAR(20) NOT NULL,
    explanation_text TEXT NOT NULL,
    technical_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '1 hour'),
    UNIQUE(stock_code, chart_period, DATE(created_at))
);
CREATE INDEX idx_ai_expires ON ai_explanations (expires_at);
CREATE INDEX idx_ai_stock_period ON ai_explanations (stock_code, chart_period);

-- 銘柄マスタテーブル
CREATE TABLE stocks (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(20) DEFAULT 'TSE',
    sector VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 株価キャッシュテーブル
CREATE TABLE stock_price_cache (
    stock_code VARCHAR(10) NOT NULL,
    price_data JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 minutes'),
    PRIMARY KEY(stock_code)
);
CREATE INDEX idx_stock_expires ON stock_price_cache (expires_at);

-- 日次API利用状況
CREATE TABLE daily_api_usage (
    usage_date DATE PRIMARY KEY,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_tokens INTEGER DEFAULT 0,
    actual_tokens INTEGER DEFAULT 0
);
CREATE INDEX idx_daily_usage_date ON daily_api_usage (usage_date DESC);

-- 分次API利用状況（レート制限）
CREATE TABLE minute_api_usage (
    minute_key VARCHAR(20) PRIMARY KEY,
    requests INTEGER DEFAULT 0,
    tokens INTEGER DEFAULT 0
);

-- ユーザー別利用状況
CREATE TABLE user_daily_usage (
    user_id UUID REFERENCES users(id),
    usage_date DATE,
    request_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    UNIQUE(user_id, usage_date)
);
CREATE INDEX idx_user_usage_date ON user_daily_usage (usage_date DESC);
CREATE INDEX idx_user_usage_user ON user_daily_usage (user_id, usage_date DESC);
```

---

**最終更新**: 2025-01-15
**バージョン**: 3.0（ユーザー登録必須版）