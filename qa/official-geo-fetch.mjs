// Fail-closed download for official GEO file in publication acceptance.
// Retry transport interruptions only; never mark a corrupt response verified.
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {setTimeout as delay} from 'node:timers/promises';

export class GeoSourceHTTPUnavailableError extends Error {
  constructor(status) {
    super('Official GEO source HTTP '+status+' (acquisition unavailable; no verified scientific input)');
    this.name = 'GeoSourceHTTPUnavailableError';
    this.status = status;
  }
}

export const isTransientTransportError = error =>
  error instanceof TypeError ||
  error instanceof GeoSourceHTTPUnavailableError ||
  error?.name === 'TimeoutError' || error?.name === 'AbortError';

export async function fetchOfficialGeoGzip(url, {
  request = globalThis.fetch, sleep = delay, retries = 2, timeoutMs = 20000,
} = {}) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await request(url, {
        signal: AbortSignal.timeout(timeoutMs),
        headers: {'User-Agent': 'BIO-MIMIC-X-live-browser-QA'},
      });
      // NCBI intermittently blocks shared CI runner IPs (HTTP 403/429/5xx).
      // Such responses never count as scientific data or a positive browser
      // test. After bounded retries, the caller records PARTIAL_SOURCE_FAILURE.
      if ([403,408,429,500,502,503,504].includes(response.status)) {
        throw new GeoSourceHTTPUnavailableError(response.status);
      }
      assert.equal(response.status, 200, 'Real GEO source required for positive E2E');
      const bytes = Buffer.from(await response.arrayBuffer());
      assert.ok(bytes.length > 1000 && bytes.length < 10000000,
        'Official GEO gzip unexpected length');
      assert.ok(bytes[0] === 0x1f && bytes[1] === 0x8b, 'Official GEO gzip header missing');
      assert.doesNotThrow(() => gunzipSync(bytes), 'Official GEO gzip incomplete or corrupted');
      return bytes;
    } catch (error) {
      const retryable = isTransientTransportError(error);
      if (!retryable || attempt === retries) throw error;
      console.warn('GEO_SOURCE_TRANSPORT_RETRY', JSON.stringify({
        attempt: attempt + 1, error: error.name, message: error.message,
      }));
      await sleep(300 * (attempt + 1));
    }
  }
}
