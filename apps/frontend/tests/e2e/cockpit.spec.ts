import { test, expect } from '@playwright/test';

test.describe('DAMGA-OPS CEO Cockpit E2E Tests', () => {
  test('E2E-01: Access 2026-06-12 (Normal & High Labor Alert Date)', async ({ page }) => {
    await page.goto('/?date=2026-06-12');
    
    // Select date 2026-06-12
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');

    // Verify Sales
    await expect(page.locator('text=13,092,000원')).toBeVisible();

    // Verify Labor Ratio 35.5% & Alert
    await expect(page.locator('text=35.5%')).toBeVisible();
    await page.getByRole('tab', { name: '오늘의 경영이상 정보' }).click();
    await expect(page.getByTestId('alert-card').getByText('인건비율 기준 초과')).toBeVisible();

    // Take Normal Day Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-NORMAL-20260612.png', fullPage: true });
  });

  test('E2E-02: Access 2026-08-21 (DATA_INCOMPLETE Date)', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-08-21');

    // Verify Warning Banner
    await expect(page.getByTestId('data-incomplete-banner')).toBeVisible();
    await expect(page.locator('text=일부 필수 데이터가 누락되었습니다')).toBeVisible();

    // Verify Independent Preserved KPIs
    await expect(page.locator('text=14,162,000원')).toBeVisible();
    await expect(page.locator('text=고객 419명')).toBeVisible();
    await expect(page.locator('text=24.5%')).toBeVisible();

    // Verify Blocked Dependent KPIs
    await expect(page.locator('text=계산 불가').first()).toBeVisible();

    // Take DATA_INCOMPLETE Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-DATA-INCOMPLETE-20260821.png', fullPage: true });
  });

  test('E2E-03: Open Evidence Drawer and Verify Cryptographic Integrity', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');
    await page.getByRole('tab', { name: '오늘의 경영이상 정보' }).click();

    // Click Evidence button on Alert
    const evButton = page.locator('button:has-text("Evidence 확인")').first();
    await expect(evButton).toBeVisible();
    await evButton.click();

    // Verify Drawer and VALID Badge
    await expect(page.getByTestId('evidence-drawer')).toBeVisible();
    await expect(page.getByTestId('evidence-status-valid')).toBeVisible();
    await expect(page.locator('text=무결성 검증됨 (VALID)')).toBeVisible();

    // Take Evidence Drawer Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-EVIDENCE-DRAWER.png', fullPage: true });
  });

  test('E2E-04: Verify 7-Day Trend Charts rendering', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('trend-charts')).toBeVisible();
    await expect(page.getByRole('heading', { name: '최근 7일 경영 추세 (7-Day Trends)', exact: true })).toBeVisible();
  });

  test('E2E-05: Tablet / Mobile Responsive Layout Viewport', async ({ page }) => {
    await page.setViewportSize({ width: 820, height: 1180 });
    await page.goto('/');

    await expect(page.getByTestId('synthetic-badge')).toBeVisible();
    await expect(page.locator('text=오늘 매출 (Sales)')).toBeVisible();

    // Take Responsive Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-RESPONSIVE-TABLET.png', fullPage: true });
  });

  test('E2E-06: Verify AI Analyst Executive Briefing on 2026-06-12', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');

    await expect(page.locator('text=AI 경영분석 및 의사결정 지원')).toBeVisible();
    await expect(page.locator('text=오늘의 결론')).toBeVisible();
    await expect(page.getByRole('heading', { name: '우선 조치', exact: true })).toBeVisible();

    // Take Analyst Briefing Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-ANALYST-BRIEF-20260612.png', fullPage: true });
  });

  test('E2E-07: Human In The Loop Approval Action Workflow', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');

    const approveBtn = page.getByRole('button', { name: '승인' });
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await expect(page.locator('text=승인 완료')).toBeVisible();
    }
  });

  test('E2E-08: AI Blocked Display on 2026-08-21 DATA_INCOMPLETE', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-08-21');

    await expect(page.locator('text=분석 차단')).toBeVisible();
    await expect(page.locator('text=필수 입력 데이터(Food_Cost)가 누락되어')).toBeVisible();
  });

  test('E2E-09: Six dashboard tabs are navigable and policy-safe', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: '오늘 매출' })).toBeVisible();
    await expect(page.getByRole('tab')).toHaveCount(6);
    await page.getByRole('tab', { name: '월 단위 매출 정보' }).click();
    await expect(page.getByTestId('monthly-sales-panel')).toBeVisible();
    await expect(page.getByText('UNVERIFIED POLICY')).toBeVisible();
    await page.getByRole('tab', { name: '연 단위 매출정보' }).click();
    await expect(page.getByTestId('yearly-sales-panel')).toBeVisible();
    await expect(page.getByText('연환산 예상 매출')).toBeVisible();
    await expect(page.locator('text=공헌이익')).toHaveCount(0);
    await expect(page.locator('text=월간 경영회의')).toHaveCount(0);
    await expect(page.locator('text=SOP ·')).toHaveCount(0);
    await page.screenshot({ path: '../../evidence/EV-UI-MANAGEMENT-PROTOTYPE.png', fullPage: true });
  });
});
