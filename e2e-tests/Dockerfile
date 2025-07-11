FROM mcr.microsoft.com/playwright:v1.40.0-focal

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# テストファイルをコピー
COPY . .

# Playwrightブラウザをインストール
RUN npx playwright install

# テスト実行コマンド
CMD ["npm", "test"]