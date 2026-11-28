// Check the default scanner mode, error handling and Swagger in a local browser.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
  const api=process.argv[2] || 'http://127.0.0.1:8000';
  const ui=process.argv[3] || 'http://127.0.0.1:8501';
  for(const url of [api,ui]) if(new URL(url).hostname!=='127.0.0.1') throw Error('Loopback required');
  const browser=await chromium.launch({executablePath:process.env.PHISHSHIELD_CHROME||undefined});
  try{
    const page=await browser.newPage({viewport:{width:1330,height:920}});
    const capabilities=await (await page.request.get(api+'/capabilities')).json();
    const live=capabilities.full_scan===true;
    await page.goto(ui);
    const fullMode=page.getByRole('radio',{name:'Full Scan',exact:true});
    await fullMode.waitFor({state:'attached'});
    if(await fullMode.isChecked()!==live) throw Error('Default scanner mode disagrees with collector readiness');
    if(!live) await page.getByText('Full Scan',{exact:true}).click();
    await page.getByRole('textbox',{name:'URL cần kiểm tra'}).fill('https://example.org/');
    await page.getByRole('button',{name:'Phân tích website'}).click();
    if(live){
      await page.getByText(/Đã tải HTML tĩnh · /).waitFor();
      await page.getByText(/Primary · random_forest · url_html · 34 đặc trưng/).waitFor();
      await page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').waitFor();
      await page.screenshot({path:path.join(__dirname,'../reports/product/screenshots/06_full_scan.png'),fullPage:true,animations:'disabled'});
    }else await page.getByText('Full Scan chưa có egress cô lập đã xác minh. Đã phân tích URL ngoại tuyến.',{exact:true}).waitFor();
    await page.getByRole('textbox',{name:'URL cần kiểm tra'}).fill('invalid');
    await page.getByRole('button',{name:'Phân tích website'}).click();
    await page.getByText('URL HTTP(S) không hợp lệ.',{exact:true}).waitFor();
    await page.goto(api+'/docs');
    const op=page.locator('.opblock').filter({has:page.locator('.opblock-summary-path[data-path="/health"]')});
    await op.locator('.opblock-summary').click();
    await op.getByRole('button',{name:'Try it out'}).click();
    const health=page.waitForResponse(r=>r.url()===api+'/health');
    await op.getByRole('button',{name:'Execute'}).click();
    const response=await health;
    if(response.status()!==200 || (await response.json()).status!=='ok') throw Error('Swagger failed');
    fs.writeFileSync(path.join(__dirname,'../reports/product/browser_modes.json'),JSON.stringify({full:live?'live HTML / primary 34':'explicit URL-only fallback',invalid:'validation error rendered',swagger:'executed GET /health: 200'},null,2));
  }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1})
