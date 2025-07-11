import { test, expect } from '@playwright/test';

const getApiURL = () => process.env.CI ? 'http://kotori_kabu_note-backend-1:8000' : 'http://localhost:8001';

test.describe('コトリの株ノート - AI機能テスト', () => {
  let authToken: string;
  
  test.beforeAll(async ({ browser }) => {
    // テスト用ユーザーでログイン
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const testUser = {
      email: `ai-user-${Date.now()}@example.com`,
      password: 'AITest123!',
      nickname: 'AI機能テストユーザー'
    };

    await page.request.post(`${getApiURL()}/auth/register`, { data: testUser });
    const loginResponse = await page.request.post(`${getApiURL()}/auth/login-json`, {
      data: { email: testUser.email, password: testUser.password }
    });
    const tokens = await loginResponse.json();
    authToken = tokens.access_token;
    
    await context.close();
  });

  test('AI解説生成機能の動作確認', async ({ page }) => {
    const explanationResponse = await page.request.post(`${getApiURL()}/ai/explain`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
      data: {
        stock_code: '7203',
        chart_period: '1M'
      }
    });

    expect(explanationResponse.status()).toBe(200);
    const explanation = await explanationResponse.json();
    
    // レスポンス構造の確認
    expect(explanation).toHaveProperty('id');
    expect(explanation).toHaveProperty('stock_code', '7203');
    expect(explanation).toHaveProperty('chart_period', '1M');
    expect(explanation).toHaveProperty('explanation_text');
    expect(explanation).toHaveProperty('technical_data');
    expect(explanation).toHaveProperty('created_at');
    expect(explanation).toHaveProperty('expires_at');

    // 解説テキストの内容確認
    expect(explanation.explanation_text).toContain('7203');
    expect(explanation.explanation_text).toContain('投資判断はご自身でお決めください');
    
    // テクニカルデータの確認
    expect(explanation.technical_data).toHaveProperty('sma_25');
    expect(explanation.technical_data).toHaveProperty('sma_75');
    expect(explanation.technical_data).toHaveProperty('rsi_14');
    expect(explanation.technical_data).toHaveProperty('macd_line');
  });

  test('AI解説のキャッシュ機能確認', async ({ page }) => {
    // 1回目の解説生成
    const firstResponse = await page.request.post(`${getApiURL()}/ai/explain`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
      data: { stock_code: '6758', chart_period: '1M' }
    });
    
    expect(firstResponse.status()).toBe(200);
    const firstExplanation = await firstResponse.json();
    
    // 2回目の同じ銘柄・期間での解説取得（キャッシュから取得されるはず）
    const secondResponse = await page.request.post(`${getApiURL()}/ai/explain`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
      data: { stock_code: '6758', chart_period: '1M' }
    });
    
    expect(secondResponse.status()).toBe(200);
    const secondExplanation = await secondResponse.json();
    
    // 同じIDであることを確認（キャッシュから取得された証拠）
    expect(secondExplanation.id).toBe(firstExplanation.id);
    expect(secondExplanation.explanation_text).toBe(firstExplanation.explanation_text);
  });

  test('AI利用制限の動作確認', async ({ page }) => {
    // 利用状況を確認
    const usageBefore = await page.request.get(`${getApiURL()}/ai/usage`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const usageDataBefore = await usageBefore.json();
    const remainingBefore = usageDataBefore.remaining_requests;

    // AI解説を1回生成
    await page.request.post(`${getApiURL()}/ai/explain`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
      data: { stock_code: '9984', chart_period: '1W' }
    });

    // 利用状況を再確認
    const usageAfter = await page.request.get(`${getApiURL()}/ai/usage`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const usageDataAfter = await usageAfter.json();
    
    // 残り回数が1回減っているか、キャッシュ使用で変化なしかを確認
    expect([remainingBefore - 1, remainingBefore]).toContain(usageDataAfter.remaining_requests);
  });

  test('認証なしでのAI機能アクセス拒否', async ({ page }) => {
    const unauthorizedResponse = await page.request.post(`${getApiURL()}/ai/explain`, {
      data: { stock_code: '7203', chart_period: '1M' }
    });

    expect(unauthorizedResponse.status()).toBe(401);
  });

  test('キャッシュされたAI解説の取得', async ({ page }) => {
    // まず解説を生成してキャッシュに保存
    await page.request.post(`${getApiURL()}/ai/explain`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
      data: { stock_code: '6861', chart_period: '3M' }
    });

    // キャッシュから取得
    const cachedResponse = await page.request.get(`${getApiURL()}/ai/explain/6861/3M`);
    
    expect(cachedResponse.status()).toBe(200);
    const cachedExplanation = await cachedResponse.json();
    expect(cachedExplanation.stock_code).toBe('6861');
    expect(cachedExplanation.chart_period).toBe('3M');
  });
});