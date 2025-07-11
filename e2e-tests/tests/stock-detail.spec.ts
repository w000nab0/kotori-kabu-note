import { test, expect } from '@playwright/test';

test.describe('コトリの株ノート - 株式詳細ページ', () => {
  test('株式詳細ページの基本要素が表示される', async ({ page }) => {
    // 直接株式詳細ページにアクセス
    await page.goto('/stocks/7203');
    
    // ローディング状態が表示される
    const loadingIndicator = page.locator('text=読み込み中...');
    if (await loadingIndicator.isVisible()) {
      await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 });
    }
    
    // 基本要素の確認
    await expect(page.locator('button:has-text("戻る")')).toBeVisible();
    await expect(page.locator('h1:has-text("7203")')).toBeVisible();
    await expect(page.locator('text=株価情報')).toBeVisible();
    
    // 期間選択ボタンの確認
    await expect(page.locator('button:has-text("1W")')).toBeVisible();
    await expect(page.locator('button:has-text("1M")')).toBeVisible();
    await expect(page.locator('button:has-text("3M")')).toBeVisible();
    await expect(page.locator('button:has-text("6M")')).toBeVisible();
    await expect(page.locator('button:has-text("1Y")')).toBeVisible();
  });

  test('株価データが正しく表示される', async ({ page }) => {
    await page.goto('/stocks/7203');
    
    // データ読み込み完了を待機
    await page.waitForTimeout(3000);
    
    // 株価が表示されることを確認（数値 + 円）
    await expect(page.locator('text=/[0-9,]+円/')).toBeVisible();
    
    // 変動率が表示されることを確認（+ or - + パーセント）
    await expect(page.locator('text=/[+-][0-9.]+%/')).toBeVisible();
  });

  test('テクニカル指標が表示される', async ({ page }) => {
    await page.goto('/stocks/7203');
    
    // データ読み込み完了を待機
    await page.waitForTimeout(3000);
    
    // テクニカル指標カードの確認
    await expect(page.locator('text=テクニカル指標')).toBeVisible();
    await expect(page.locator('text=SMA25')).toBeVisible();
    await expect(page.locator('text=SMA75')).toBeVisible();
    await expect(page.locator('text=RSI(14)')).toBeVisible();
    await expect(page.locator('text=MACD')).toBeVisible();
  });

  test('チャートプレースホルダーが表示される', async ({ page }) => {
    await page.goto('/stocks/7203');
    
    // チャートセクションの確認
    await expect(page.locator('text=株価チャート')).toBeVisible();
    await expect(page.locator('text=チャート表示（実装予定）')).toBeVisible();
  });

  test('AI解説セクションが表示される', async ({ page }) => {
    await page.goto('/stocks/7203');
    
    // AI解説カードの確認
    await expect(page.locator('text=AI解説')).toBeVisible();
    await expect(page.locator('text=AIがチャートの状況をやさしく解説します')).toBeVisible();
    
    // ログインしていない場合のメッセージを確認
    const loginMessage = page.locator('text=AI解説を見るにはログインが必要です');
    const generateButton = page.locator('button:has-text("AI解説を生成")');
    
    // どちらかが表示されることを確認
    await expect(loginMessage.or(generateButton)).toBeVisible();
  });

  test('期間選択機能が動作する', async ({ page }) => {
    await page.goto('/stocks/7203');
    
    // 初期状態で1Mが選択されていることを確認
    await expect(page.locator('button:has-text("1M")')).toHaveClass(/(?:bg-|default)/);
    
    // 3Mボタンをクリック
    await page.locator('button:has-text("3M")').click();
    
    // データ再読み込みを待機
    await page.waitForTimeout(2000);
    
    // 3Mが選択状態になることを確認
    await expect(page.locator('button:has-text("3M")')).toHaveClass(/(?:bg-|default)/);
  });

  test('戻るボタンが機能する', async ({ page }) => {
    // ホームページから株式詳細ページに遷移
    await page.goto('/');
    
    // 最初の株式カードをクリック
    const firstStockCard = page.locator('.cursor-pointer').first();
    await firstStockCard.click();
    
    // 詳細ページに到達することを確認
    await page.waitForURL('**/stocks/**');
    
    // 戻るボタンをクリック
    await page.locator('button:has-text("戻る")').click();
    
    // ホームページに戻ることを確認
    await page.waitForURL('/');
    await expect(page.locator('h2')).toContainText('投資初心者のための');
  });

  test('存在しない銘柄コードでもエラーが発生しない', async ({ page }) => {
    await page.goto('/stocks/9999');
    
    // ページが読み込まれることを確認
    await expect(page.locator('button:has-text("戻る")')).toBeVisible();
    await expect(page.locator('h1:has-text("9999")')).toBeVisible();
    
    // エラーメッセージではなく、基本的なレイアウトが表示される
    await expect(page.locator('text=株価情報')).toBeVisible();
  });
});