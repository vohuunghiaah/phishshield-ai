// Exercise online/offline capability gating and the Swagger operation on a deployed instance.
const assert = require('node:assert/strict');
const { openBrowser, scan, settle } = require('./check_ui.cjs');

(async () => {
  const api = process.argv[2] || 'http://127.0.0.1:8000';
  if (new URL(api).hostname !== '127.0.0.1') throw Error('Local API required');
  const { browser, page } = await openBrowser(process.argv[3] || 'http://127.0.0.1:8501');
  try {
    const live = (await (await page.request.get(api + '/capabilities')).json()).full_scan;
    if (live) {
      assert.ok(await page.getByRole('radio', { name: 'Full Scan', exact: true }).isChecked());
      await scan(page, 'https://example.org/');
      await page.getByText(/URL và HTML tự thu thập · 34 đặc trưng/).waitFor();
      await settle(page);
      await scan(page, 'https://fullscan-fixture.invalid/');
      await page.getByText(/Website không trả về HTML/).waitFor();
      await page.getByText(/Chỉ URL · 17 đặc trưng/).waitFor();
    } else {
      assert.equal(await page.getByRole('radio', { name: 'Full Scan' }).count(), 0);
      assert.ok(await page.getByRole('radio', { name: 'Quick Scan' }).isChecked());
    }
    await scan(page, 'invalid');
    await page.getByText('URL HTTP(S) không hợp lệ.', { exact: true }).waitFor();
    await page.goto(api + '/docs');
    const op = page.locator('.opblock').filter({ has: page.locator('.opblock-summary-path[data-path="/health"]') });
    await op.locator('.opblock-summary').click();
    await op.getByRole('button', { name: 'Try it out' }).click();
    const response = page.waitForResponse(r => r.url() === api + '/health');
    await op.getByRole('button', { name: 'Execute' }).click();
    assert.equal((await (await response).json()).status, 'ok');
    console.log('Verified capability gating, validation and Swagger; full_scan=' + live);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
