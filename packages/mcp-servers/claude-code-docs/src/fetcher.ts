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

    const content = await response.text();
    return { content, status: response.status };
  } catch (err: unknown) {
    const anyErr = err as { name?: string; message?: string };
    if (anyErr?.name === 'AbortError') {
      throw new FetchTimeoutError(`Fetch timeout after ${resolvedTimeoutMs}ms`);
    }
    if (err instanceof FetchHttpError) {
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
