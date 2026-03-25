import path from 'node:path';
import { describe, it, expect } from 'vitest';
import { loadConfig } from '../src/config.js';

function makeEnv(overrides: Record<string, string | undefined> = {}): NodeJS.ProcessEnv {
  return {
    ...overrides,
  };
}

describe('loadConfig', () => {
  it('returns defaults when env is empty', () => {
    const config = loadConfig(makeEnv());
    expect(config.docsUrl).toBe('https://code.claude.com/docs/llms-full.txt');
    expect(config.retryIntervalMs).toBe(60000);
  });

  it('parses valid runtime overrides', () => {
    const config = loadConfig(
      makeEnv({
        DOCS_URL: 'https://example.com/docs/llms-full.txt',
        RETRY_INTERVAL_MS: '120000',
        CACHE_TTL_MS: '5000',
        DOCS_CACHE_MAX_STALE_MS: '9000',
        MIN_SECTION_COUNT: '10',
        MAX_INDEX_CACHE_BYTES: '123456',
        FETCH_TIMEOUT_MS: '2000',
        MAX_RESPONSE_BYTES: '9999',
      }),
    );

    expect(config.docsUrl).toBe('https://example.com/docs/llms-full.txt');
    expect(config.retryIntervalMs).toBe(120000);
  });

  it('rejects non-https DOCS_URL', () => {
    expect(() =>
      loadConfig(makeEnv({ DOCS_URL: 'http://example.com/docs' })),
    ).toThrow(/DOCS_URL must use https/);
  });

  it('rejects retry interval below minimum', () => {
    expect(() =>
      loadConfig(makeEnv({ RETRY_INTERVAL_MS: '999' })),
    ).toThrow(/RETRY_INTERVAL_MS must be >= 1000/);
  });

  it('rejects retry interval above maximum', () => {
    expect(() =>
      loadConfig(makeEnv({ RETRY_INTERVAL_MS: '600001' })),
    ).toThrow(/RETRY_INTERVAL_MS must be <= 600000/);
  });

  it('rejects CACHE_PATH without filename', () => {
    expect(() =>
      loadConfig(makeEnv({ CACHE_PATH: `${path.sep}tmp${path.sep}cache${path.sep}` })),
    ).toThrow(/CACHE_PATH must include a filename/);
  });

  it('rejects invalid numeric env consumed by lower layers', () => {
    expect(() =>
      loadConfig(makeEnv({ MAX_RESPONSE_BYTES: '12.5' })),
    ).toThrow(/MAX_RESPONSE_BYTES must be an integer/);
  });
});
