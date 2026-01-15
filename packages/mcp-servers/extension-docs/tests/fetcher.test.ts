import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchOfficialDocs,
  FetchTimeoutError,
  FetchHttpError,
  FetchNetworkError,
} from '../src/fetcher.js';

describe('fetchOfficialDocs', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns content on successful fetch', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve('doc content'),
    });
    vi.stubGlobal('fetch', mockFetch);

    const result = await fetchOfficialDocs('https://example.com/docs');
    expect(result.content).toBe('doc content');
    expect(result.status).toBe(200);
  });

  it('throws FetchHttpError on 404', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: new Headers(),
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/missing')).rejects.toThrow(
      FetchHttpError
    );
  });

  it('throws FetchTimeoutError on abort', async () => {
    const mockFetch = vi.fn().mockImplementation(() => {
      const error = new Error('aborted');
      error.name = 'AbortError';
      return Promise.reject(error);
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/slow', 100)).rejects.toThrow(
      FetchTimeoutError
    );
  });

  it('throws FetchNetworkError on network failure', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('ECONNREFUSED'));
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/down')).rejects.toThrow(
      FetchNetworkError
    );
  });
});
