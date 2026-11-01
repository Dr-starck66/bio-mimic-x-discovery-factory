import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import test from 'node:test';
import {fetchOfficialGeoGzip,isTransientTransportError} from './official-geo-fetch.mjs';

const source = gzipSync(randomBytes(2400));
const response = bytes => ({status: 200, arrayBuffer: async () => bytes});
const noSleep = async () => {};

test('recovers after one network termination, retaining exact bytes', async () => {
  let calls = 0;
  const request = async () => (++calls === 1
    ? Promise.reject(new TypeError('terminated')) : response(source));
  const bytes = await fetchOfficialGeoGzip('https://example.invalid/gse.gz',
    {request, sleep: noSleep});
  assert.deepEqual(bytes, source);
  assert.equal(calls, 2);
});

test('fails closed after three transport failures', async () => {
  let calls = 0;
  const request = async () => {calls++; throw new TypeError('terminated');};
  await assert.rejects(fetchOfficialGeoGzip('https://example.invalid/gse.gz',
    {request, sleep: noSleep}), /terminated/);
  assert.equal(calls, 3);
});

test('rejects HTTP 503 instead of claiming verified input', async () => {
  let calls = 0;
  const request = async () => {calls++; return {status: 503};};
  await assert.rejects(fetchOfficialGeoGzip('https://example.invalid/gse.gz',
    {request, sleep: noSleep}), /Real GEO source required/);
  assert.equal(calls, 1);
});

test('rejects truncated gzip with valid magic header', async () => {
  const request = async () => response(source.subarray(0, 1100));
  await assert.rejects(fetchOfficialGeoGzip('https://example.invalid/gse.gz',
    {request, sleep: noSleep}), /Official GEO gzip incomplete or corrupted/);
});

test('accepts intact gzip without retry', async () => {
  let calls = 0;
  const request = async () => {calls++; return response(source);};
  assert.deepEqual(await fetchOfficialGeoGzip('https://example.invalid/gse.gz',
    {request, sleep: noSleep}), source);
  assert.equal(calls, 1);
});

test('degrade only exhausted network transport, not invalid source data', () => {
  assert.equal(isTransientTransportError(new TypeError('terminated')),true);
  assert.equal(isTransientTransportError({name:'TimeoutError'}),true);
  assert.equal(isTransientTransportError({name:'AbortError'}),true);
  assert.equal(isTransientTransportError(new Error('truncated gzip')),false);
  assert.equal(isTransientTransportError(new Error('HTTP 404')),false);
});
