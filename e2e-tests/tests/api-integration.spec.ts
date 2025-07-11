import { test, expect } from '@playwright/test';

const getApiURL = () => process.env.CI ? 'http://kotori_kabu_note-backend-1:8000' : 'http://localhost:8001';

test.describe('コトリの株ノート - API統合テスト', () => {
  test('バックエンドAPIが正常に応答する', async ({ page }) => {
    // ヘルスチェックエンドポイントをテスト
    const response = await page.request.get(`${getApiURL()}/health`);
    expect(response.status()).toBe(200);
    
    const healthData = await response.json();
    expect(healthData).toHaveProperty('status', 'healthy');
  });

  test('株式検索APIが正常に動作する', async ({ page }) => {
    // 株式検索APIをテスト
    const response = await page.request.get(`${getApiURL()}/stocks/search?q=7203`);
    expect(response.status()).toBe(200);
    
    const searchData = await response.json();
    expect(Array.isArray(searchData)).toBeTruthy();
    
    if (searchData.length > 0) {
      expect(searchData[0]).toHaveProperty('code');
      expect(searchData[0]).toHaveProperty('name');
      expect(searchData[0]).toHaveProperty('sector');
    }
  });

  test('株価データAPIが正常に動作する', async ({ page }) => {
    // 株価データAPIをテスト
    const response = await page.request.get(`${getApiURL()}/stocks/7203/price?period=1M`);
    expect(response.status()).toBe(200);
    
    const priceData = await response.json();
    expect(priceData).toHaveProperty('stock_code', '7203');
    expect(priceData).toHaveProperty('period', '1M');
    expect(priceData).toHaveProperty('data');
    expect(Array.isArray(priceData.data)).toBeTruthy();
    
    if (priceData.data.length > 0) {
      const firstDataPoint = priceData.data[0];
      expect(firstDataPoint).toHaveProperty('time');
      expect(firstDataPoint).toHaveProperty('open');
      expect(firstDataPoint).toHaveProperty('high');
      expect(firstDataPoint).toHaveProperty('low');
      expect(firstDataPoint).toHaveProperty('close');
      expect(firstDataPoint).toHaveProperty('volume');
    }
  });

  test('テクニカル指標APIが正常に動作する', async ({ page }) => {
    // テクニカル指標APIをテスト
    const response = await page.request.get(`${getApiURL()}/stocks/7203/indicators?period=1M`);
    expect(response.status()).toBe(200);
    
    const indicators = await response.json();
    expect(indicators).toHaveProperty('sma_25');
    expect(indicators).toHaveProperty('sma_75');
    expect(indicators).toHaveProperty('rsi_14');
    expect(indicators).toHaveProperty('macd_line');
    expect(indicators).toHaveProperty('macd_signal');
    expect(indicators).toHaveProperty('macd_histogram');
  });

  test('ユーザー登録APIが正常に動作する', async ({ page }) => {
    const testUser = {
      email: `test-${Date.now()}@example.com`,
      password: 'testpass123',
      nickname: 'テストユーザー'
    };

    // ユーザー登録APIをテスト
    const response = await page.request.post(`${getApiURL()}/auth/register`, {
      data: testUser
    });
    
    expect(response.status()).toBe(200);
    
    const userData = await response.json();
    expect(userData).toHaveProperty('email', testUser.email);
    expect(userData).toHaveProperty('nickname', testUser.nickname);
    expect(userData).toHaveProperty('id');
  });

  test('フロントエンドからバックエンドへの通信が正常に動作する', async ({ page }) => {
    await page.goto('/');
    
    // ネットワークリクエストを監視
    const apiRequests: any[] = [];
    page.on('request', request => {
      if (request.url().includes(getApiURL().replace('http://', ''))) {
        apiRequests.push({
          url: request.url(),
          method: request.method()
        });
      }
    });

    // 検索を実行してAPIコールを発生させる
    await page.locator('input[placeholder*="銘柄コード"]').fill('7203');
    await page.locator('button:has-text("検索する")').click();
    
    // APIリクエストが発生することを確認
    await page.waitForTimeout(2000);
    
    // 検索APIが呼び出されたことを確認
    const searchRequest = apiRequests.find(req => 
      req.url.includes('/stocks/search') && req.method === 'GET'
    );
    expect(searchRequest).toBeTruthy();
  });

  test('CORS設定が正しく動作する', async ({ page }) => {
    // フロントエンドからのリクエストが正常に処理される
    await page.goto('/');
    
    // APIリクエストが成功することを確認（CORSエラーが発生しない）
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch(`${getApiURL()}/health`);
        return { status: res.status, ok: res.ok };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    expect(response.status).toBe(200);
    expect(response.ok).toBe(true);
  });
});