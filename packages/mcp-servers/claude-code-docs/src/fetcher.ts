export interface FetchResult {
  content: string;
  status: number;
}

export class FetchTimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FetchTimeoutError';
  }
}

export class FetchHttpError extends Error {
  status: number;
  statusText?: string;

  constructor(status: number, statusText?: string) {
    const message = statusText ? `HTTP ${status}: ${statusText}` : `HTTP ${status}`;
    super(message);
    this.name = 'FetchHttpError';
    this.status = status;
    this.statusText = statusText;
  }
}

export class FetchNetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FetchNetworkError';
  }
}

export class FetchResponseTooLargeError extends Error {
  byteLimit: number;
  constructor(byteLimit: number, actual?: number) {
    const msg = actual
      ? `Response too large: ${actual} bytes exceeds ${byteLimit} byte limit`
      : `Response too large: exceeds ${byteLimit} byte limit`;
    super(msg);
    this.name = 'FetchResponseTooLargeError';
    this.byteLimit = byteLimit;
  }
}

const DEFAULT_MAX_RESPONSE_BYTES = 10 * 1024 * 1024; // 10MB

function resolveMaxResponseBytes(): number {
  const envValue = process.env.MAX_RESPONSE_BYTES?.trim();
  if (envValue) {
    const parsed = parseInt(envValue, 10);
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }
  return DEFAULT_MAX_RESPONSE_BYTES;
}

async function readResponseWithLimit(response: Response, maxBytes: number): Promise<string> {
  const reader = response.body?.getReader();
  if (!reader) {
    // Fallback if no body stream (shouldn't happen with Node 18+ fetch)
    return response.text();
  }

  const decoder = new TextDecoder();
  const chunks: string[] = [];
  let totalBytes = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      totalBytes += value.byteLength;
      if (totalBytes > maxBytes) {
        reader.cancel();
        throw new FetchResponseTooLargeError(maxBytes);
      }

      chunks.push(decoder.decode(value, { stream: true }));
    }
  } finally {
    reader.releaseLock();
  }

  // Flush decoder
  chunks.push(decoder.decode());
  return chunks.join('');
}

function resolveTimeoutMs(explicit?: number): number {
  if (typeof explicit === 'number' && Number.isFinite(explicit) && explicit >= 0) {
    return explicit;
  }
  const envValue = process.env.FETCH_TIMEOUT_MS?.trim();
  if (envValue && envValue.length > 0) {
    const parsed = Number(envValue);
    if (Number.isFinite(parsed) && parsed >= 0) {
      return parsed;
    }
  }
  return 30000;
}

export async function fetchOfficialDocs(
  url: string,
  timeoutMs?: number
): Promise<FetchResult> {
  const resolvedTimeoutMs = resolveTimeoutMs(timeoutMs);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), resolvedTimeoutMs);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      redirect: 'follow',
    });

    if (!response.ok) {
      const statusText = response.statusText || undefined;
      throw new FetchHttpError(response.status, statusText);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType && !contentType.toLowerCase().startsWith('text/')) {
      console.warn(`Unexpected content-type for ${url}: ${contentType}`);
    }

    const maxBytes = resolveMaxResponseBytes();

    // Fast reject if Content-Length header exceeds limit
    const contentLength = response.headers.get('content-length');
    if (contentLength) {
      const declaredBytes = parseInt(contentLength, 10);
      if (Number.isFinite(declaredBytes) && declaredBytes > maxBytes) {
        throw new FetchResponseTooLargeError(maxBytes, declaredBytes);
      }
    }

    // Stream body with byte limit (handles chunked encoding where Content-Length is absent)
    const content = await readResponseWithLimit(response, maxBytes);
    return { content, status: response.status };
  } catch (err: unknown) {
    const anyErr = err as { name?: string; message?: string };
    if (anyErr?.name === 'AbortError') {
      throw new FetchTimeoutError(`Fetch timeout after ${resolvedTimeoutMs}ms`);
    }
    if (err instanceof FetchHttpError || err instanceof FetchResponseTooLargeError) {
      throw err;
    }
    if (anyErr?.message) {
      throw new FetchNetworkError(`Network error: ${anyErr.message}`);
    }
    throw new FetchNetworkError('Network error: Unknown error');
  } finally {
    clearTimeout(timeoutId);
  }
}
