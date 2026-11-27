// Run against the local Streamlit service with Playwright installed.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const url = process.argv[2] || 'http://127.0.0.1:8501';
  if (!['127.0.0.1','localhost'].includes(new URL(url).hostname)) throw Error('Loopback UI required');
  const out = path.join(__dirname, '../reports/product/screenshots');
  fs.mkdirSync(out,{recursive:true});
  const browser = await chromium.launch({headless:true,executablePath:process.env.PHISHSHIELD_CHROME || undefined});
  try {
    const page = await browser.newPage({viewport:{width:1330,height:920},deviceScaleFactor:1});
    await page.goto(url);
    const shot = async name => {
      await page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').waitFor();
      await page.locator('[data-stale="true"]').first().waitFor({state:'hidden'});
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({path:path.join(out,name+'.png'),fullPage:true,animations:'disabled'});
    };
    await page.getByRole('textbox',{name:'URL cần kiểm tra'}).fill('https://example.org/');
    await page.getByRole('button',{name:'Phân tích website',exact:true}).click();
    await page.getByText(/Fallback · random_forest/).waitFor();
    await shot('01_url_fallback');
    await page.getByText('Phân tích nâng cao',{exact:true}).first().click();
    await page.getByRole('textbox',{name:'URL cần kiểm tra'}).fill('https://example.org/');
    await page.getByRole('textbox',{name:'HTML snapshot'}).fill('<html><title>Example</title><p>Local fixture</p></html>');
    await page.getByRole('button',{name:'Phân tích website',exact:true}).click();
    await page.getByText(/Primary · random_forest/).waitFor();
    await shot('02_html_primary');
    await page.getByText('Giải thích',{exact:true}).first().click();
    await page.getByRole('heading',{name:'Giải thích',exact:true}).waitFor();
    await page.getByRole('textbox',{name:'HTML snapshot'}).waitFor({state:'hidden'});
    await page.getByText('Các yếu tố đóng góp',{exact:true}).waitFor();
    await shot('03_explanation');
    await page.getByText('Hiệu năng',{exact:true}).first().click();
    await page.getByText('98.422%',{exact:true}).waitFor();
    await page.getByText('Fallback URL-only chưa có đánh giá Test riêng.').waitFor();
    await shot('04_locked_test');
    await page.setViewportSize({width:390,height:844});
    const sidebar = page.getByTestId('stSidebar');
    if (await sidebar.getAttribute('aria-expanded') === 'true') {
      await page.getByTestId('stSidebarCollapseButton').getByRole('button').click();
    }
    await page.waitForFunction(() => document.querySelector('[data-testid="stSidebar"]').getBoundingClientRect().right <= 1);
    await page.getByText('Hiệu năng trên tập Test',{exact:true}).waitFor();
    await shot('05_mobile');
    console.log('Browser UI completed: URL, snapshot, explanation, metrics, narrow viewport');
  } finally { await browser.close(); }
})().catch(err=>{console.error(err);process.exitCode=1;});

