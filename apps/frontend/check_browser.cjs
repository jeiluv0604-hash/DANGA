
const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('BROWSER PAGE ERROR:', err.message));
  page.on('requestfailed', req => console.error('REQUEST FAILED:', req.url(), req.failure().errorText));
  
  await page.goto('http://127.0.0.1:3000');
  await page.waitForTimeout(3000);
  console.log('PAGE TITLE:', await page.title());
  await browser.close();
})();
