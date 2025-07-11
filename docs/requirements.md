# 📈 AIチャート分析アプリ 機能要件書（株式版）
#アプリ名 : コトリの株ノート

---

## 🌟 共通コンセプト

### 🌸 ターゲットユーザー
- 投資初心者の女性（20〜40代）
- スマホで気軽に株価チャートを見たい層

### 💡 アプリの特徴
- スマートフォン中心のレスポンシブデザイン
- 落ち着いた色調（パステルカラー・グレージュ・優しいダークモード）
- ChatGPTではなく **Gemini 2.0 Flash-Lite API** を使用
- **広告表示なし**

---

## 🧭 機能一覧（株式版）

### 📌 メイン機能

- 🔍 **銘柄検索**
  - 銘柄コード・企業名で検索可能
  - オートサジェスト対応（例：「とよ」→「7203 トヨタ自動車」）
  - 最近検索した銘柄の履歴機能（100件まで保存）

- 💡 **銘柄提案（おすすめリスト）**
  - 業種別や人気ランキングをもとに初心者向け銘柄をリストアップ
  - 「配当利回りが高い」「安定成長中」などフィルタ可能
  - 🔖 **ブックマーク機能**
  - よく見る銘柄をお気に入り登録
  - ブックマーク一覧からクイックアクセス

- 📊 **チャート表示（Lightweight Charts）**
  - ローソク足（日足・週足両対応）
  - 出来高表示あり

- 🔁 **期間切替**
  - 1週間 / 1ヶ月 / 3ヶ月 / 6ヶ月 / 1年

- 📈 **テクニカル指標表示（MVP版）**
  - 単純移動平均線（SMA）：25日・75日
  - RSI：14日設定
  - MACD：デフォルト設定
  - 出来高：25日平均と比較
  - 表示ON/OFF切替機能

- 🤖 **AIチャート解説（Gemini 2.0 Flash-Lite）**
  - 指標に基づく自然言語解説
  - 投資初心者向けにわかりやすい文体
  - コメント例：「最近は横ばいですね。焦らず見守りましょう。」
  - 「投資判断はご自身で」などの免責コメントを自動添付
  - **利用制限：1日10回まで（無料枠内運用のため）**

### 👤 **ユーザー管理**
- **会員登録必須**
  - メールアドレス + パスワードでの簡単登録
  - メール認証による本人確認
  - 登録後すぐに全機能利用可能
  - 利用制限：
    - 銘柄検索：無制限
    - AI解説：1日10回まで
    - 検索履歴：100件まで保存

---

## 📱 UI設計ポイント

- スマホ片手で操作しやすい大きめボタン（48px以上）
- チャート中心の画面構成
- コメントはふきだし風、フェードインアニメーション
- 検索・指標切り替えはタブ or スライド式

---

## 🔧 バックエンド・技術構成

- データ取得：yfinance（Python）
- AI API：Gemini 2.0 Flash-Lite（オンデマンド生成）
- API制限管理：トークンベース精密制限（無料枠内運用）
- ユーザー認証システム（メール認証）
- 軽量キャッシュ（株価データ30分、AI解説1時間）
- データ更新頻度：30分毎
- セッション管理（ログイン状態維持）

---

## 🔒 リスク対策・法的注意点

- 「これは投資助言ではありません」など免責表示
- 利確・損切りなどの売買判断は表示しない
- Gemini 2.0 Flash-Liteのコメントは「状況説明」「参考意見」に限定

---

## 🚀 将来の拡張（オプション）

- 類似チャートパターン表示（AI判定）
- 銘柄のフォロー・ブックマーク機能
- テーマ別スクリーニング（例：「高配当」「ESG関連」）
- 有料APIへの切替機構（J-Quantsなど）

---

## ✅ 最小構成（MVP）

1. ユーザー登録・ログイン機能（メール認証）
2. 銘柄検索 + チャート表示（日足・週足）
3. テクニカル指標表示（SMA 25日・75日、RSI 14日、MACD、出来高）
4. Gemini 2.0 Flash-Liteによるやさしいチャート解説（1日10回まで）
5. API制限管理システム（無料枠内運用）
6. スマホ向けUIで操作がしやすい
7. 完全無料・広告なし・免責つき
8. 検索履歴・ユーザー設定保存
