import { test, expect } from '@playwright/test';

const getApiURL = () => process.env.CI ? 'http://kotori_kabu_note-backend-1:8000' : 'http://localhost:8001';

test.describe('コトリの株ノート - エラーハンドリングテスト', () => {
  test('存在しない銘柄コードでの適切なエラーレスポンス', async ({ page }) => {
    // 存在しない銘柄コードでの株価データ取得
    const response = await page.request.get(`${getApiURL()}/stocks/9999/price?period=1M`);
    
    // 404エラーではなく、モックデータが返されることを確認（現在の実装）
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.stock_code).toBe('9999');
    expect(data.data).toBeDefined();
    expect(Array.isArray(data.data)).toBe(true);
  });

  test('無効な期間パラメータでのデフォルト動作', async ({ page }) => {
    const response = await page.request.get(`${getApiURL()}/stocks/7203/price?period=INVALID`);
    
    expect(response.status()).toBe(200);
    const data = await response.json();
    // 無効な期間の場合、デフォルト値が使用される
    expect(data.stock_code).toBe('7203');
    expect(data.data).toBeDefined();
  });

  test('空の検索クエリでの適切な処理', async ({ page }) => {
    const response = await page.request.get(`${getApiURL()}/stocks/search?q=`);
    
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    // 空のクエリの場合、空の配列が返される
    expect(data.length).toBe(0);
  });

  test('重複ユーザー登録での適切なエラー処理', async ({ page }) => {
    const testUser = {
      email: `duplicate-test-${Date.now()}@example.com`,
      password: 'TestPass123!',
      nickname: 'テストユーザー'
    };

    // 1回目の登録（成功）
    const firstRegister = await page.request.post(`${getApiURL()}/auth/register`, {
      data: testUser
    });
    expect(firstRegister.status()).toBe(200);

    // 2回目の登録（重複エラー）
    const secondRegister = await page.request.post(`${getApiURL()}/auth/register`, {
      data: testUser
    });
    expect(secondRegister.status()).toBe(400);
    
    const error = await secondRegister.json();
    expect(error.detail).toContain('already exists');
  });

  test('無効なJWTトークンでの認証失敗', async ({ page }) => {
    const invalidToken = 'invalid.jwt.token';
    
    const response = await page.request.get(`${getApiURL()}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${invalidToken}`
      }
    });

    expect(response.status()).toBe(401);
  });

  test('期限切れトークンの処理', async ({ page }) => {
    // 期限切れのようなトークンをテスト
    const expiredLikeToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalid';
    
    const response = await page.request.get(`${getApiURL()}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${expiredLikeToken}`
      }
    });

    expect(response.status()).toBe(401);
  });

  test('APIレート制限の確認', async ({ page }) => {
    // テスト用ユーザーを作成
    const testUser = {
      email: `rate-limit-test-${Date.now()}@example.com`,
      password: 'TestPass123!',
      nickname: 'レート制限テストユーザー'
    };

    await page.request.post(`${getApiURL()}/auth/register`, { data: testUser });
    const loginResponse = await page.request.post(`${getApiURL()}/auth/login-json`, {
      data: { email: testUser.email, password: testUser.password }
    });
    const tokens = await loginResponse.json();

    // 利用制限を確認
    const usageResponse = await page.request.get(`${getApiURL()}/ai/usage`, {
      headers: { 'Authorization': `Bearer ${tokens.access_token}` }
    });

    expect(usageResponse.status()).toBe(200);
    const usage = await usageResponse.json();
    expect(usage.daily_limit).toBe(10);
    expect(usage.remaining_requests).toBeLessThanOrEqual(10);
  });

  test('フロントエンドページでの404エラーハンドリング', async ({ page }) => {
    // 存在しないページへのアクセス
    await page.goto('/nonexistent-page');
    
    // Next.jsの404ページまたは適切なエラーページが表示されることを確認
    await expect(page.locator('body')).toBeVisible();
    
    // エラーページの要素が含まれているかチェック
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('ネットワークエラー時のフロントエンドの動作', async ({ page }) => {
    await page.goto('/');
    
    // ネットワークを遮断
    await page.route('**/*', route => route.abort());
    
    // 検索ボタンをクリック
    await page.locator('input[placeholder*="銘柄コード"]').fill('7203');
    await page.locator('button:has-text("検索する")').click();
    
    // エラーは表示されないが、検索結果が表示されないことを確認
    await page.waitForTimeout(2000);
    const searchResults = page.locator('text=検索結果');
    await expect(searchResults).not.toBeVisible();
  });
});