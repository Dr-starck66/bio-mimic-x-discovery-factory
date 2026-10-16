#!/usr/bin/env node
// Live-provider Chromium smoke: no intercepts or synthetic results.
import assert from 'node:assert/strict';
import {chromium} from 'playwright-core';

const origin=process.env.BIOMIMIC_TEST_URL || 'http://127.0.0.1:8765';
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
const page=await browser.newPage();
const errs=[];
page.on('pageerror',e=>errs.push(String(e)));
try{
  await page.goto(origin+'/hunter.html',{waitUntil:'load',timeout:15000});
  await page.locator('#problem').fill('regeneration');
  await page.locator('#years').selectOption('10');
  await page.locator('#runHunter').click();
  await page.waitForFunction(()=>{
    const s=document.querySelector('#providerStatus')?.textContent||'';
    return s.includes('Europe PMC: pass')||s.includes('Europe PMC: fail');
  },null,{timeout:47000});
  const provider=(await page.locator('#providerStatus').textContent()).trim();
  assert.match(provider,/Europe PMC: pass/,'Europe PMC browser-level live request failed: '+provider);
  const titles=await page.locator('#paperGrid .card h4').allTextContents();
  assert.ok(titles.length>=1,'Live provider returned no articles to the UI');
  assert.ok(await page.locator('#dlReplay').count()===1,'Live replay missing');
  assert.equal(errs.length,0,'Browser JS errors: '+errs.join('; '));
  console.log(JSON.stringify({
    status:'PASS',kind:'LIVE_BROWSER_EUROPE_PMC',
    paper_cards:titles.length,synthetic_provider_fixture:false,
    independent_scientific_validation:false
  }));
}catch(e){
  console.error('LIVE-BROWSER-FAIL',e.stack||String(e));
  process.exitCode=1;
}finally{await browser.close()}
