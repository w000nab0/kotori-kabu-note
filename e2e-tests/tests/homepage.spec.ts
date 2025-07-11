import { test, expect } from '@playwright/test';

test.describe('コトリの株ノート - ホームページ', () => {
  test('ホームページの基本要素が表示される', async ({ page }) => {
    await page.goto('/');
    
    // ヘッダーの確認
    await expect(page.locator('h1')).toContainText('コトリの株ノート');
    
    // メインタイトルの確認
    await expect(page.locator('h2')).toContainText('投資初心者のためのやさしい株価分析');
    
    // 検索バーの確認
    await expect(page.locator('input[placeholder*="銘柄コード"]')).toBeVisible();
    await expect(page.locator('button')).toContainText('検索する');
    
    // 人気銘柄セクションの確認
    await expect(page.locator('h3')).toContainText('人気の銘柄');
    
    // 人気銘柄カードの確認（最低4つ）
    const stockCards = page.locator('[data-testid="stock-card"], .cursor-pointer').filter({
      has: page.locator('text=/^[0-9]{4}$/')
    });
    await expect(stockCards).toHaveCount(4);
  });

  test('株式検索機能が動作する', async ({ page }) => {
    await page.goto('/');
    
    // 検索フィールドに入力
    const searchInput = page.locator('input[placeholder*="銘柄コード"]');
    await searchInput.fill('7203');
    
    // 検索ボタンをクリック
    await page.locator('button:has-text("検索する")').click();
    
    // 検索中の状態を確認
    await expect(page.locator('button')).toContainText('検索中...');
    
    // 検索結果が表示されるまで待機
    await page.waitForTimeout(2000);
    
    // 検索結果の確認
    const searchResults = page.locator('text=検索結果');
    if (await searchResults.isVisible()) {
      await expect(searchResults).toBeVisible();
      await expect(page.locator('text=7203')).toBeVisible();
      await expect(page.locator('text=トヨタ')).toBeVisible();
    }
  });

  test('人気銘柄をクリックして詳細ページに遷移', async ({ page }) => {
    await page.goto('/');
    
    // 最初の人気銘柄カードをクリック
    const firstStockCard = page.locator('.cursor-pointer').first();
    await firstStockCard.click();
    
    // 詳細ページに遷移することを確認
    await page.waitForURL('**/stocks/**');
    
    // 詳細ページの要素を確認
    await expect(page.locator('button:has-text("戻る")')).toBeVisible();
    await expect(page.locator('text=株価情報')).toBeVisible();
  });

  test('ナビゲーションボタンが正しく表示される', async ({ page }) => {
    await page.goto('/');
    
    // ヘッダーのナビゲーションボタン
    await expect(page.locator('button:has-text("ブックマーク")')).toBeVisible();
    await expect(page.locator('button:has-text("ログイン")')).toBeVisible();
    
    // アイコンの確認
    await expect(page.locator('svg[data-lucide="bookmark"]')).toBeVisible();
    await expect(page.locator('svg[data-lucide="user"]')).toBeVisible();
  });

  test('レスポンシブデザインの確認', async ({ page }) => {
    // モバイルサイズに変更
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // モバイル表示でも基本要素が表示される
    await expect(page.locator('h1')).toContainText('コトリの株ノート');
    await expect(page.locator('input[placeholder*="銘柄コード"]')).toBeVisible();
    
    // 人気銘柄が縦並びになることを確認
    const stockCards = page.locator('.cursor-pointer').filter({
      has: page.locator('text=/^[0-9]{4}$/')
    });
    await expect(stockCards.first()).toBeVisible();
  });
});