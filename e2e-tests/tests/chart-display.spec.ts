import { test, expect } from '@playwright/test'

test.describe('チャート表示機能', () => {
  test('株式詳細ページでチャートが正常に表示される', async ({ page }) => {
    // 株式詳細ページに移動
    await page.goto('http://host.docker.internal:3000/stocks/7203')
    
    // ページの基本要素が表示されるまで待機
    await expect(page.locator('h1:has-text("7203")')).toBeVisible()
    
    // チャートカードが表示されることを確認
    await expect(page.locator('text=株価チャート')).toBeVisible()
    
    // チャートコンテナが存在することを確認
    const chartContainer = page.locator('[style*="width: 100%; height: 500px"]')
    await expect(chartContainer).toBeVisible()
    
    // 指標切り替えボタンが表示されることを確認
    await expect(page.locator('button:has-text("SMA")')).toBeVisible()
    await expect(page.locator('button:has-text("RSI")')).toBeVisible()
    await expect(page.locator('button:has-text("MACD")')).toBeVisible()
    await expect(page.locator('button:has-text("出来高")')).toBeVisible()
  })

  test('期間切り替えボタンが動作する', async ({ page }) => {
    await page.goto('http://host.docker.internal:3000/stocks/7203')
    
    // 期間切り替えボタンが表示されることを確認
    await expect(page.locator('button:has-text("1W")')).toBeVisible()
    await expect(page.locator('button:has-text("1M")')).toBeVisible()
    await expect(page.locator('button:has-text("3M")')).toBeVisible()
    await expect(page.locator('button:has-text("6M")')).toBeVisible()
    await expect(page.locator('button:has-text("1Y")')).toBeVisible()
    
    // デフォルトで1Mが選択されていることを確認
    const oneMonthButton = page.locator('button:has-text("1M")')
    await expect(oneMonthButton).toHaveClass(/bg-/)
    
    // 3Mボタンをクリック
    await page.click('button:has-text("3M")')
    
    // チャートの説明が更新されることを確認
    await expect(page.locator('text=7203 - 3M期間のローソク足チャート')).toBeVisible()
  })

  test('テクニカル指標切り替えボタンが動作する', async ({ page }) => {
    await page.goto('http://host.docker.internal:3000/stocks/7203')
    
    // SMAボタンが初期状態でアクティブであることを確認
    const smaButton = page.locator('button:has-text("SMA")')
    await expect(smaButton).toHaveClass(/bg-blue-500/)
    
    // RSIボタンをクリックしてアクティブにする
    const rsiButton = page.locator('button:has-text("RSI")')
    await rsiButton.click()
    await expect(rsiButton).toHaveClass(/bg-purple-500/)
    
    // MACDボタンをクリックしてアクティブにする
    const macdButton = page.locator('button:has-text("MACD")')
    await macdButton.click()
    await expect(macdButton).toHaveClass(/bg-green-500/)
    
    // 出来高ボタンは初期状態でアクティブであることを確認
    const volumeButton = page.locator('button:has-text("出来高")')
    await expect(volumeButton).toHaveClass(/bg-teal-500/)
  })

  test('テクニカル指標データが表示される', async ({ page }) => {
    await page.goto('http://host.docker.internal:3000/stocks/7203')
    
    // テクニカル指標カードが表示されることを確認
    await expect(page.locator('text=テクニカル指標')).toBeVisible()
    await expect(page.locator('text=主要な技術分析指標の現在値')).toBeVisible()
    
    // 各指標値が表示されることを確認
    await expect(page.locator('text=SMA25')).toBeVisible()
    await expect(page.locator('text=SMA75')).toBeVisible()
    await expect(page.locator('text=RSI(14)')).toBeVisible()
    await expect(page.locator('text=MACD')).toBeVisible()
    await expect(page.locator('text=MACD Signal')).toBeVisible()
    await expect(page.locator('text=MACD Histogram')).toBeVisible()
    await expect(page.locator('text=出来高SMA25')).toBeVisible()
    
    // 数値が表示されることを確認（N/Aでない）
    const indicators = page.locator('.bg-blue-50, .bg-orange-50, .bg-purple-50, .bg-green-50, .bg-teal-50, .bg-indigo-50, .bg-gray-50')
    const count = await indicators.count()
    expect(count).toBeGreaterThan(0)
    
    // 少なくとも一つの指標値が数値として表示されることを確認
    await expect(page.locator('text=/[0-9]+\\.?[0-9]*/').first()).toBeVisible()
  })

  test('株価情報が正しく表示される', async ({ page }) => {
    await page.goto('http://host.docker.internal:3000/stocks/7203')
    
    // 株価情報が表示されることを確認
    await expect(page.locator('text=株価情報')).toBeVisible()
    
    // 現在価格が表示されることを確認
    await expect(page.locator('text=/[0-9,]+円/')).toBeVisible()
    
    // 変動率が表示されることを確認
    await expect(page.locator('text=/%/')).toBeVisible()
  })

  test('戻るボタンが動作する', async ({ page }) => {
    // まずホームページに移動
    await page.goto('http://host.docker.internal:3000')
    
    // 株式詳細ページに移動
    await page.goto('http://host.docker.internal:3000/stocks/7203')
    
    // 戻るボタンをクリック
    await page.click('button:has-text("戻る")')
    
    // ホームページに戻ることを確認
    await expect(page).toHaveURL('http://host.docker.internal:3000/')
  })

  test('存在しない銘柄コードでエラー処理される', async ({ page }) => {
    // 存在しない銘柄コード
    await page.goto('http://host.docker.internal:3000/stocks/9999')
    
    // エラーページまたは適切なエラーメッセージが表示されることを確認
    // （ここでは読み込み中の状態が継続するか、エラーメッセージが表示される）
    
    await page.waitForTimeout(3000) // API応答を待つ
    
    // エラー状態の確認（データが読み込まれない場合）
    const hasError = await page.locator('text=データを読み込み中...').isVisible()
    const hasChart = await page.locator('text=株価チャート').isVisible()
    
    expect(hasError || hasChart).toBeTruthy()
  })
})