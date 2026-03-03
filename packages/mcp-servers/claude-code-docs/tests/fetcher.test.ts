import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchOfficialDocs,
  FetchTimeoutError,
  FetchHttpError,
  FetchNetworkError,
  FetchResponseTooLargeError,
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

describe('response size limits', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
    // Set a small limit for testing (1KB)
    vi.stubEnv('MAX_RESPONSE_BYTES', '1024');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('rejects responses exceeding Content-Length limit', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({
        'content-type': 'text/plain',
        'content-length': '2048',
      }),
      body: null,
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/large')).rejects.toThrow(
      FetchResponseTooLargeError,
    );
    await expect(fetchOfficialDocs('https://example.com/large')).rejects.toThrow(
      /2048 bytes exceeds 1024 byte limit/,
    );
  });

  it('rejects streaming responses exceeding byte limit', async () => {
    // Create a ReadableStream that yields 2KB of data
    const largeData = new Uint8Array(2048).fill(65); // 'A' bytes
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(largeData);
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      body: stream,
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/chunked')).rejects.toThrow(
      FetchResponseTooLargeError,
    );
  });

  it('accepts responses within size limit', async () => {
    const smallData = new TextEncoder().encode('small content');
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(smallData);
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      body: stream,
    });
    vi.stubGlobal('fetch', mockFetch);

    const result = await fetchOfficialDocs('https://example.com/small');
    expect(result.content).toBe('small content');
    expect(result.status).toBe(200);
  });

  it('allows Content-Length within limit', async () => {
    const data = new TextEncoder().encode('ok');
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(data);
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({
        'content-type': 'text/plain',
        'content-length': '2',
      }),
      body: stream,
    });
    vi.stubGlobal('fetch', mockFetch);

    const result = await fetchOfficialDocs('https://example.com/ok');
    expect(result.content).toBe('ok');
  });
});
