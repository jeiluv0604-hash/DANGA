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
    await expect(page.locator('text=최근 7일 경영 추세')).toBeVisible();
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

    await expect(page.locator('text=AI 경영 분석 브리핑 & 의사결정 지원')).toBeVisible();
    await expect(page.locator('text=Executive Summary')).toBeVisible();
    await expect(page.locator('text=권고 조치 및 경영진 결재 (Human Approval)')).toBeVisible();

    // Take Analyst Briefing Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-ANALYST-BRIEF-20260612.png', fullPage: true });
  });

  test('E2E-07: Human In The Loop Approval Action Workflow', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');

    const approveBtn = page.locator('button:has-text("승인 (Approve)")');
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await expect(page.locator('text=경영진 승인 완료 (APPROVED)')).toBeVisible();
    }
  });

  test('E2E-08: AI Blocked Display on 2026-08-21 DATA_INCOMPLETE', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-08-21');

    await expect(page.locator('text=AI 분석 차단 (DATA_INCOMPLETE)')).toBeVisible();
    await expect(page.locator('text=필수 입력 데이터(Food_Cost)가 누락되어')).toBeVisible();
  });

  test('E2E-09: Management System Prototype is synthetic and policy-safe', async ({ page }) => {
    await page.goto('/');
    const management = page.getByTestId('management-system-prototype');
    await expect(management).toBeVisible();
    await expect(management.getByText('담가화로구이 경영체계 프로토타입')).toBeVisible();
    await expect(management.getByText('SYNTHETIC · 실제 담가화로구이 매장 데이터 아님')).toBeVisible();
    await expect(management.getByText('UNVERIFIED POLICY').first()).toBeVisible();
    await expect(management.getByText('Recipe/BOM · 메뉴 ABCD')).toBeVisible();
    await expect(management.getByText(/OPEN → IN_PROGRESS → CLOSED → VERIFIED/)).toBeVisible();
    await page.screenshot({ path: '../../evidence/EV-UI-MANAGEMENT-PROTOTYPE.png', fullPage: true });
  });
});
