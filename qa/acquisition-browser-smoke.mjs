#!/usr/bin/env node
import assert from 'node:assert/strict';
import {chromium} from 'playwright-core';

const origin=process.env.BIOMIMIC_TEST_URL || 'http://127.0.0.1:8765';
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
const errors=[];
const page=await browser.newPage();
page.on('pageerror',e=>errors.push(String(e)));
const checks=[];
try{
  const resp=await page.goto(origin+'/buyer-demo.html',{waitUntil:'load'});
  assert.equal(resp.status(),200);
  assert.match(await page.title(),/BIO-MIMIC X/);
  checks.push('loads');
  const body=await page.locator('body').innerText();
  for(const term of ['129','Europe PMC','€1,000,000','seller asking price','FAIL','UNVERIFIED','not a validated biological therapy']){
    assert.ok(body.toLowerCase().includes(term.toLowerCase()),'Missing real evidence/boundary '+term);
  }
  checks.push('evidence_and_price_disclaimers');
  assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'),'noindex,nofollow');
  checks.push('non_indexed_buyer_overview');
  await page.locator('#openHunter').click();
  assert.match(await page.locator('h1').first().innerText(),/BIO-MIMIC X/);
  assert.equal((await page.locator('#runHunter').count()),1);
  checks.push('working_hunter_link');
  await page.goto(origin+'/buyer-demo.html');
  await page.locator('#openCenter').click();
  assert.ok(await page.locator('#factoryStatus').count()===1);
  checks.push('working_dashboard_link');
  const mobile=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  mobile.on('pageerror',e=>errors.push(String(e)));
  await mobile.goto(origin+'/buyer-demo.html');
  const overflow=await mobile.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
  assert.ok(overflow<=2,'Horizontal mobile overflow: '+overflow);
  assert.ok(await mobile.locator('#openHunter').isVisible());
  checks.push('mobile_no_horizontal_overflow');
  // GEO evidence is a separate product feature, not a new scientific PASS.
  await page.goto(origin+'/science-validation.html',{waitUntil:'load'});
  await page.waitForFunction(()=>document.querySelector('#originalStatus')?.textContent?.includes('FAIL'),{timeout:10000});
  assert.ok((await page.locator('#preflightStatus').innerText()).includes('NOT COMPARABLE'),'GSE159938 must not be falsely passed');
  const rows=await page.locator('#cohortRows tr').count();
  assert.equal(rows,2,'Both historical cohorts must be shown');
  assert.equal(await page.locator('#export').isDisabled(),true,'No report before user file verification');
  await page.locator('#upload').setInputFiles({name:'fake.soft.gz',mimeType:'application/gzip',buffer:Buffer.from('FAKE_GEO_DATA')});
  await page.locator('#verify').click();
  assert.ok((await page.locator('#localStatus').innerText()).includes('UNVERIFIED'),'Tampered input must be rejected');
  assert.equal(await page.locator('#export').isDisabled(),true,'Tampered input must not enable export');
  checks.push('geo_science_evidence_viewer','geo_sha256_negative_control');
  await page.goto(origin+'/buyer-demo.html');
  assert.equal(await page.locator('#openScienceAudit').count(),1,'Buyer must be able to open science audit');
  await page.goto(origin+'/');
  assert.equal(await page.locator('#scienceEvidenceLink').count(),1,'Dashboard must link to GEO evidence audit');
  checks.push('geo_audit_navigation');
  assert.equal(errors.length,0,'JS errors '+errors.join('; '));
  checks.push('no_runtime_errors');
  console.log(JSON.stringify({status:'PASS',kind:'ACQUISITION_TECHNICAL_DEMO',checks,real_lab_validation_claim:false,third_party_valuation_claim:false}));
}catch(e){
  console.error('ACQUISITION-DEMO-FAIL',e.stack||String(e));
  process.exitCode=1;
}finally{await browser.close()}
