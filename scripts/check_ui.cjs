// Exercise the deployed UI against real inference. Usage: node scripts/check_ui.cjs [local UI] [screenshot directory]
const { chromium } = require('playwright');

const fs = require('node:fs');
const path = require('node:path');

async function openBrowser(url) {
  if (!['127.0.0.1', 'localhost'].includes(new URL(url).hostname)) throw Error('Local UI required');
  const browser = await chromium.launch({ executablePath: process.env.PHISHSHIELD_CHROME || undefined });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(url);
  await page.getByRole('textbox', { name: 'Địa chỉ website' }).waitFor();
  return { browser, page };
}

async function settle(page) {
  await page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').waitFor();
  await page.locator('[data-stale="true"]').first().waitFor({ state: 'hidden' });
  await page.evaluate(() => document.fonts.ready);
}

async function scan(page, url) {
  await page.getByRole('textbox', { name: 'Địa chỉ website' }).fill(url);
  await page.getByRole('button', { name: 'Phân tích', exact: true }).click();
}

async function checkUI() {
  const { browser, page } = await openBrowser(process.argv[2] || 'http://127.0.0.1:8501');
  const out = process.argv[3] || path.join(__dirname, '../reports/ui_v2/screenshots/desktop');
  fs.mkdirSync(out, { recursive: true });
  async function shot(name) {
    await settle(page);
    await page.screenshot({ path: path.join(out, name + '.png'), animations: 'disabled' });
  }
  try {
    await page.getByRole('link', { name: /Báo cáo phân tích/ }).click();
    await page.getByText(/Chưa có kết quả trong phiên này/).waitFor();
    await page.getByRole('link', { name: /Mở công cụ phân tích/ }).click();
    await page.getByText('Quick Scan', { exact: true }).click();
    await scan(page, 'https://example.org/');
    await page.getByText(/Chỉ URL · 17 đặc trưng/).waitFor();
    await page.getByText('0,052', { exact: true }).waitFor();
    await shot('quick');
    await page.getByText('Snapshot Analysis (nâng cao)', { exact: true }).click();
    await page.getByRole('textbox', { name: 'Nội dung HTML' }).fill('<html><title>Example</title><p>Local fixture</p><script type="text/plain">inert</script></html>');
    await scan(page, 'https://example.org/');
    await page.getByText(/URL và HTML cung cấp · 34 đặc trưng/).waitFor();
    await shot('snapshot');
    await page.getByRole('link', { name: /Báo cáo phân tích/ }).click();
    await page.getByRole('heading', { name: 'Dấu hiệu ảnh hưởng' }).waitFor();
    await page.locator('.signal').first().waitFor();
    await page.getByText('Chi tiết kỹ thuật', { exact: true }).click();
    await page.getByText(/Checkpoint 0a78a47a3a46/).waitFor();
    await page.getByRole('link', { name: /Hiệu năng mô hình/ }).click();
    await page.getByRole('table', { name: 'Ma trận nhầm lẫn' }).waitFor();
    await page.getByText('96,102%', { exact: true }).waitFor();
    await shot('performance');
    await page.getByRole('link', { name: /[Hh]ướng dẫn/ }).click();
    await page.getByRole('heading', { name: 'Giới thiệu và hướng dẫn' }).waitFor();
    console.log('Verified report navigation, Quick, Snapshot, contributions, locked Test and guide.');
  } finally { await browser.close(); }
}

module.exports = { openBrowser, scan, settle };
if (require.main === module) checkUI().catch(e => { console.error(e); process.exitCode = 1; });
