// Exercise the fallback notice, invalid input and Swagger through a real local browser.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
  const api=process.argv[2] || 'http://127.0.0.1:8000';
  const ui=process.argv[3] || 'http://127.0.0.1:8501';
  for(const url of [api,ui]) if(new URL(url).hostname!=='127.0.0.1') throw Error('Loopback required');
  const browser=await chromium.launch({executablePath:process.env.PHISHSHIELD_CHROME||undefined});
  try{
    const page=await browser.newPage();
    await page.goto(ui);
    await page.getByText('Full Scan',{exact:true}).click();
    await page.getByRole('textbox',{name:'URL cần kiểm tra'}).fill('https://example.org/');
    await page.getByRole('button',{name:'Phân tích website'}).click();
    await page.getByText('Full Scan chưa có egress cô lập đã xác minh. Đã phân tích URL ngoại tuyến.',{exact:true}).waitFor();
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
    fs.writeFileSync(path.join(__dirname,'../reports/product/browser_modes.json'),JSON.stringify({full:'explicit URL-only fallback',invalid:'validation error rendered',swagger:'executed GET /health: 200'},null,2));
  }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1})

