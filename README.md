# 📈 コトリの株ノート

投資初心者向けのAI株価分析アプリ

## 🌟 概要

コトリの株ノートは、投資初心者の女性（20〜40代）をターゲットにした、スマートフォン中心のレスポンシブな株価分析アプリです。

### 主な機能
- 📊 株価チャート表示（TradingView Lightweight Charts）
- 🤖 AI による投資初心者向けチャート解説（Gemini 2.0 Flash-Lite）
- 🔍 銘柄検索・オートサジェスト
- 🔖 ブックマーク機能
- 💡 おすすめ銘柄リスト
- 📈 テクニカル指標（SMA, MACD, RSI, 出来高）

## 🛠️ 技術スタック

### Frontend
- Next.js 15 + React 18 + TypeScript
- Tailwind CSS v3 + shadcn/ui
- TradingView Lightweight Charts

### Backend
- FastAPI + Python 3.11+
- yfinance（株価データ取得）
- Gemini 2.0 Flash-Lite API

### Database & Infrastructure
- Supabase PostgreSQL
- Vercel（フロントエンド）
- Render（バックエンド）

## 📁 プロジェクト構造

```
kotori_kabu_note/
├── frontend/          # Next.js アプリケーション
├── backend/           # FastAPI アプリケーション
├── docs/             # 仕様書・ドキュメント
└── docker-compose.yml # ローカル開発環境
```

## 🚀 開発環境セットアップ

### 前提条件
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### セットアップ手順

1. リポジトリクローン
```bash
git clone [repository-url]
cd kotori_kabu_note
```

2. フロントエンド
```bash
cd frontend
npm install
npm run dev
```

3. バックエンド
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

4. Docker環境（推奨）
```bash
docker-compose up -d
```

## 🔑 環境変数

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret
```

## 📊 API制限管理

- **Gemini 2.0 Flash-Lite**: 200 requests/日（安全マージン85%）
- **ユーザー制限**: 1日10回のAI解説
- **株価データ**: 15-20分遅延（yfinance）

## 🔒 セキュリティ

- JWT認証（Access: 1時間, Refresh: 7日間）
- bcrypt パスワードハッシュ化
- メール認証必須
- レート制限実装

## 📝 ライセンス

MIT License

## 👥 開発者

- AI Assistant with Claude Code

---

**免責事項**: このサービスは投資助言・勧誘を目的としたものではありません。投資判断は必ずご自身の責任において行ってください。