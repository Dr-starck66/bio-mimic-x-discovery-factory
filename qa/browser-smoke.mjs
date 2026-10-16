#!/usr/bin/env node
// Real Chromium UI acceptance, deterministic offline fixtures for external providers.
// Does NOT represent a live-provider or independent laboratory validation.
import assert from 'node:assert/strict';
import {readFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright-core';

const origin=process.env.BIOMIMIC_TEST_URL || 'http://127.0.0.1:8765';
const records=[1,2,3].map(n=>({
  id:'fixture-00'+n, source:'TEST',
  title:'Synthetic fixture '+n+': comparative Wnt and Ficticia exemplaris',
  abstractText:'Ficticia exemplaris is a synthetic testing name only. Observational fibrosis and Wnt pathways, no established mechanism.',
  pubYear:'2025', citedByCount:'2'
}));
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
const context=await browser.newContext({acceptDownloads:true,viewport:{width:1360,height:920}});
const page=await context.newPage();
const pageErrors=[];
page.on('pageerror', e=>pageErrors.push(String(e)));
let failApi=false;
async function check(condition, message){ assert.ok(condition,message); }
async function screenshotOnFail(){
  await mkdir('qa-artifacts',{recursive:true});
  try{await page.screenshot({path:'qa-artifacts/browser-failure.png',fullPage:true});}catch{}
}
async function text(selector){return page.locator(selector).textContent()}

try{
  await page.route('**/webservices/rest/search?**', route=>
    failApi ? route.fulfill({status:503,body:'Service unavailable'}) :
    route.fulfill({status:200,contentType:'application/json',
      body:JSON.stringify({resultList:{result:records}})})
  );
  await page.route('**/annotations_api/**',route=>route.fulfill({
    status:200,contentType:'application/json',
    body:JSON.stringify({annotations:[{exact:'Ficticia exemplaris'}]})
  }));
  await page.goto(origin+'/hunter.html',{waitUntil:'load',timeout:20000});
  assert.match(await text('h1'),/BIO-MIMIC X/);
  assert.notEqual((await text('#kBricks')).trim(),'—');
  assert.ok(await page.locator('#brickGrid .brick').count()>=8,'Bricks missing');

  await page.locator('nav [data-tab="atlas"]').click();
  assert.ok(await page.locator('#atlasGrid .card').count()>8,'Atlas empty');
  await page.locator('#atlasQ').fill('Axolotl');
  assert.ok((await text('#atlasGrid')).includes('Axolotl'),'Atlas filter broken');
  await page.locator('nav [data-tab="hunter"]').click();

  await page.locator('#problem').fill('Synthetic fibrosis test');
  await page.locator('#runHunter').click();
  await page.locator('#dlReplay').waitFor({timeout:30000});
  assert.ok((await text('#candidateGrid')).includes('Ficticia exemplaris'),'Hunter missed fixture species');
  assert.ok((await text('#paperGrid')).includes('fixture-001')===false,'Test must render paper title, not internal identifier');
  assert.ok((await text('#experimentOut')).includes('Ficticia exemplaris'),'Experiment forge failed');
  await page.locator('#candidateGrid .inspect').first().click();
  assert.ok((await text('#morpheusOut')).includes('MORPHEUS'),'Adversarial audit failed');

  await page.locator('#enrich').click();
  await page.waitForFunction(()=>document.querySelector('#claimGrid')?.textContent?.includes('PLAUSIBLE'),{timeout:15000});
  const claims=await text('#claimGrid');
  assert.ok(!claims.includes('VERIFIED'),'Annotation alone must never certify an independent scientific discovery');

  const [download]=await Promise.all([
    page.waitForEvent('download',{timeout:15000}),
    page.locator('nav [data-tab="mission"]').click().then(()=>page.locator('#dlReplay').click())
  ]);
  const json=JSON.parse(await readFile(await download.path(),'utf8'));
  assert.ok(json.sha256?.length===64,'Missing replay SHA256');
  const expected=json.sha256;
  delete json.sha256;
  assert.equal(createHash('sha256').update(JSON.stringify(json)).digest('hex'),expected,
    'Replay export SHA does not match its payload');
  assert.ok(json.papers.length===3,'Fixture papers lost in replay');

  await page.locator('nav [data-tab="hunter"]').click();
  page.once('dialog',dialog=>dialog.accept('synthetic negative control'));
  await page.locator('#candidateGrid .reject').first().click();
  await page.locator('nav [data-tab="evidence"]').click();
  assert.ok((await text('#negativeGrid')).includes('synthetic negative control'),'Negative Knowledge absent');
  await page.reload();
  await page.locator('nav [data-tab="evidence"]').click();
  assert.ok((await text('#negativeGrid')).includes('synthetic negative control'),'Negative Knowledge not persisted');

  failApi=true;
  await page.locator('nav [data-tab="hunter"]').click();
  await page.locator('#problem').fill('Fault injection');
  await page.locator('#runHunter').click();
  await page.waitForFunction(()=>document.querySelector('#providerStatus')?.textContent?.includes('Europe PMC: fail'),{timeout:30000});
  assert.ok((await text('#paperGrid')).includes('Pas de littérature live'),'Failure fallback is not observable');

  await page.goto(origin+'/',{waitUntil:'load',timeout:25000});
  await page.waitForFunction(()=>document.querySelector('#factoryStatus')?.textContent!=='—',{timeout:30000});
  const factoryStatus=(await text('#factoryStatus')).trim();
  assert.notEqual(factoryStatus,'OFFLINE','Dashboard cannot read factory status');
  const link=page.locator('a[href="./hunter.html"]');
  assert.equal(await link.count(),1,'Control Center is not linked to the Hunter');
  await link.click();
  assert.match(await text('h1'),/BIO-MIMIC X/);

  const mobile=await browser.newContext({viewport:{width:390,height:844}});
  const mobilePage=await mobile.newPage();
  await mobilePage.goto(origin+'/hunter.html',{waitUntil:'load',timeout:20000});
  assert.ok(await mobilePage.locator('#runHunter').count()===1,'Mobile hunter unavailable');
  await mobile.close();

  assert.equal(pageErrors.length,0,'Browser JS exceptions: '+pageErrors.join('; '));
  console.log(JSON.stringify({
    status:'PASS',kind:'CHROMIUM_UI_MOCKED_PROVIDERS',
    checks:['hunter_boot','navigation','atlas_filter','search','morpheus',
      'annotations_without_false_verification','replay_download_sha256',
      'negative_knowledge_persistence','provider_failure','dashboard_data',
      'dashboard_hunter_link','mobile_render'],
    synthetic_provider_fixture:true,live_provider_validation:false
  }));
} catch(e) {
  await screenshotOnFail();
  console.error('BROWSER-ACCEPTANCE-FAIL',e.stack||String(e));
  process.exitCode=1;
} finally {
  await browser.close();
}
