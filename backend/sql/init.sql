-- コトリの株ノート データベース初期化スクリプト

-- ユーザー管理テーブル
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
CREATE INDEX idx_email ON users (email);

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