#!/usr/bin/env node
// Verify the independently hosted immutable release in an actual Chromium browser.
// This is software/publication acceptance, NOT independent scientific validation.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright-core';

const base='https://duality-x-eco.floot.app';
const endpoint=base+'/_api/biomimic?path=';
const expectedSha='790378bf759f421b103bfeb3f39bc273a3652cc8';
const fixture=[1,2,3].map(n=>({
  id:'fixture-00'+n,source:'TEST',
  title:'Synthetic fixture '+n+': comparative Wnt and Ficticia exemplaris',
  abstractText:'Ficticia exemplaris is a synthetic testing name only. Observational fibrosis and Wnt pathways, no established mechanism.',
  pubYear:'2025',citedByCount:'2'
}));
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
const context=await browser.newContext({acceptDownloads:true,viewport:{width:1300,height:900}});
const page=await context.newPage();
const errors=[];
page.on('pageerror',e=>errors.push(String(e)));
try{
  await page.route('**/webservices/rest/search?**',route=>route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify({resultList:{result:fixture}})
  }));
  const r=await page.goto(endpoint+'hunter.html',{waitUntil:'load',timeout:30000});
  assert.equal(r?.status(),200,'Hosted Hunter HTTP status');
  assert.equal(r?.headers()['x-biomimic-source-commit'],expectedSha,'Hosted release must be pinned to tested SHA');
  assert.match(await page.locator('h1').textContent(),/BIO-MIMIC X/);
  assert.ok(await page.locator('#brickGrid .brick').count()>=8,'Hosted Hunter JS failed to initialize');

  await page.locator('#problem').fill('Synthetic fibrosis test');
  await page.locator('#runHunter').click();
  await page.locator('#dlReplay').waitFor({state:'attached',timeout:30000});
  assert.ok((await page.locator('#candidateGrid').textContent()).includes('Ficticia exemplaris'));
  const [download]=await Promise.all([
    page.waitForEvent('download',{timeout:20000}),
    page.locator('nav [data-tab="mission"]').click().then(()=>page.locator('#dlReplay').click())
  ]);
  const payload=JSON.parse(await readFile(await download.path(),'utf8'));
  assert.equal(payload.papers.length,3,'Hosted UI lost synthetic fixture');
  assert.equal(payload.sha256?.length,64);
  const expected=payload.sha256;
  delete payload.sha256;
  assert.equal(createHash('sha256').update(JSON.stringify(payload)).digest('hex'),expected,'Hosted replay SHA mismatch');

  const dash=await page.goto(endpoint+'index.html',{waitUntil:'load',timeout:30000});
  assert.equal(dash?.status(),200);
  assert.equal(dash?.headers()['x-biomimic-source-commit'],expectedSha);
  assert.match(await page.locator('h1').textContent(),/BIO-MIMIC X/);
  await page.waitForFunction(()=>document.querySelector('#factoryStatus')?.textContent!=='—',null,{timeout:50000});
  assert.notEqual((await page.locator('#factoryStatus').textContent()).trim(),'OFFLINE','Hosted dashboard data unavailable');
  const link=page.locator('a[href="/_api/biomimic?path=hunter.html"]');
  assert.equal(await link.count(),1,'Hosted internal Hunter link broken');
  await link.click();
  assert.match(await page.locator('h1').textContent(),/BIO-MIMIC X/);
  const bio=await page.goto(endpoint+'science-validation.html',{waitUntil:'load',timeout:30000});
  assert.equal(bio?.status(),200,'Scientific audit product publicly accessible');
  assert.equal(bio?.headers()['x-biomimic-source-commit'],expectedSha);
  await page.waitForFunction(()=>document.querySelector('#originalStatus')?.textContent?.includes('FAIL'),null,{timeout:15000});
  assert.ok((await page.locator('#preflightStatus').textContent()).includes('NOT COMPARABLE'),
    'No false scientific PASS in publicly hosted evidence audit');
  assert.equal(await page.locator('#cohortRows tr').count(),2,'Both preregistered cohorts must be visible');
  await page.locator('#upload').setInputFiles({name:'tampered.soft.gz',mimeType:'application/gzip',buffer:Buffer.from('NOT_GEO')});
  await page.locator('#verify').click();
  await page.waitForFunction(()=>document.querySelector('#localStatus')?.textContent?.includes('UNVERIFIED'),null,{timeout:10000});
  assert.equal(await page.locator('#export').isDisabled(),true,'Tampered file must not be downloadable as verified');
  const official='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE159nnn/GSE159938/soft/GSE159938_family.soft.gz';
  const officialFetch=await fetch(official,{signal:AbortSignal.timeout(20000),headers:{'User-Agent':'BIO-MIMIC-X-live-browser-QA'}});
  assert.equal(officialFetch.status,200,'Real GEO source required for positive E2E');
  const officialBytes=Buffer.from(await officialFetch.arrayBuffer());
  assert.ok(officialBytes.length>1000&&officialBytes.length<10000000,'Official GEO gzip unexpected length');
  await page.locator('#upload').setInputFiles({name:'GSE159938_family.soft.gz',mimeType:'application/gzip',buffer:officialBytes});
  await page.locator('#verify').click();
  await page.waitForFunction(()=>document.querySelector('#localStatus')?.textContent?.includes('AUDIT LOCAL TERMINÉ'),null,{timeout:10000});
  const verified=JSON.parse(await page.locator('#localDetails').textContent());
  assert.equal(verified.status,'NOT_COMPARABLE_ORIGINAL_TIMEPOINTS_AND_STRATA');
  assert.equal(verified.sample_count,25);
  assert.equal(verified.by_species.Acomys,12);
  assert.equal(verified.by_species.Mus,13);
  assert.equal(verified.compatible_six_cell_strata,0);
  assert.equal(verified.biological_validation,'UNVERIFIED');
  assert.equal(await page.locator('#export').isDisabled(),false,'Verified GEO input must enable report export');
  const [auditDownload]=await Promise.all([page.waitForEvent('download',{timeout:20000}),page.locator('#export').click()]);
  const exported=JSON.parse(await readFile(await auditDownload.path(),'utf8'));
  assert.equal(exported.input_sha256,verified.input_sha256);
  assert.equal(exported.status,verified.status,'Export status must equal displayed conclusion');

  const original=await page.goto(base+'/',{waitUntil:'load',timeout:30000});
  assert.equal(original?.status(),200);
  assert.ok((await page.locator('body').textContent()).includes('DUALITY'),'Original host app was changed');

  assert.equal(errors.length,0,'Hosted browser JS exceptions: '+errors.join('; '));
  console.log(JSON.stringify({
    status:'PASS',kind:'PUBLICATION_BROWSER_FLOOT_EXISTING_HOST',sourceSha:expectedSha,
    checks:['https_200','mime_and_sha_header','hunter_init','fixture_search','replay_sha256',
      'dashboard_live_json','dashboard_link','geo_science_audit_live','geo_negative_sha_guard','geo_real_ncbi_upload_25_samples','geo_report_export_integrity','original_host_unmodified'],
    independent_scientific_validation:false
  }));
}catch(e){
  console.error('PUBLICATION-BROWSER-FAIL',e.stack||String(e));
  process.exitCode=1;
}finally{
  await browser.close();
}
