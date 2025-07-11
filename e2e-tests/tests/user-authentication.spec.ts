import { test, expect } from '@playwright/test';

const getApiURL = () => process.env.CI ? 'http://kotori_kabu_note-backend-1:8000' : 'http://localhost:8001';

test.describe('コトリの株ノート - ユーザー認証フロー', () => {
  test.beforeEach(async ({ page }) => {
    // 各テスト前にローカルストレージをクリア
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('ユーザー登録からログインまでの完全フロー', async ({ page }) => {
    const testUser = {
      email: `test-${Date.now()}@example.com`,
      password: 'SecurePass123!',
      nickname: 'テストユーザー'
    };

    // 1. ユーザー登録API
    const registerResponse = await page.request.post(`${getApiURL()}/auth/register`, {
      data: testUser
    });
    
    expect(registerResponse.status()).toBe(200);
    const userData = await registerResponse.json();
    expect(userData.email).toBe(testUser.email);
    expect(userData.nickname).toBe(testUser.nickname);
    expect(userData).toHaveProperty('id');

    // 2. ログインAPI
    const loginResponse = await page.request.post(`${getApiURL()}/auth/login-json`, {
      data: {
        email: testUser.email,
        password: testUser.password
      }
    });

    expect(loginResponse.status()).toBe(200);
    const tokens = await loginResponse.json();
    expect(tokens).toHaveProperty('access_token');
    expect(tokens).toHaveProperty('refresh_token');
    expect(tokens.token_type).toBe('bearer');

    // 3. 認証が必要なエンドポイントへのアクセス
    const protectedResponse = await page.request.get(`${getApiURL()}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`
      }
    });

    expect(protectedResponse.status()).toBe(200);
    const userInfo = await protectedResponse.json();
    expect(userInfo.email).toBe(testUser.email);
  });

  test('無効な認証情報でのログイン失敗', async ({ page }) => {
    const invalidLogin = await page.request.post(`${getApiURL()}/auth/login-json`, {
      data: {
        email: 'nonexistent@example.com',
        password: 'wrongpassword'
      }
    });

    expect(invalidLogin.status()).toBe(401);
    const error = await invalidLogin.json();
    expect(error.detail).toBe('Incorrect email or password');
  });

  test('AIサービス利用制限の確認', async ({ page }) => {
    // ユーザー登録とログイン
    const testUser = {
      email: `ai-test-${Date.now()}@example.com`,
      password: 'TestPass123!',
      nickname: 'AIテストユーザー'
    };

    await page.request.post(`${getApiURL()}/auth/register`, { data: testUser });
    const loginResponse = await page.request.post(`${getApiURL()}/auth/login-json`, {
      data: { email: testUser.email, password: testUser.password }
    });
    const tokens = await loginResponse.json();

    // AI利用状況確認
    const usageResponse = await page.request.get(`${getApiURL()}/ai/usage`, {
      headers: { 'Authorization': `Bearer ${tokens.access_token}` }
    });

    expect(usageResponse.status()).toBe(200);
    const usage = await usageResponse.json();
    expect(usage.allowed).toBe(true);
    expect(usage.daily_limit).toBe(10);
    expect(usage.remaining_requests).toBeLessThanOrEqual(10);
  });
});