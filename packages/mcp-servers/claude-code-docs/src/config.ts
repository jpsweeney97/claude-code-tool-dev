import path from 'node:path';

const DEFAULT_DOCS_URL = 'https://code.claude.com/docs/llms-full.txt';
const DEFAULT_RETRY_INTERVAL_MS = 60000;
const MIN_RETRY_INTERVAL_MS = 1000;
const MAX_RETRY_INTERVAL_MS = 600000;

export interface AppConfig {
  docsUrl: string;
  retryIntervalMs: number;
}

function formatInput(input: unknown): string {
  const serialized = typeof input === 'string' ? input : JSON.stringify(input);
  const safe = serialized ?? String(input);
  const truncated = safe.length > 100 ? `${safe.slice(0, 100)}...` : safe;
  return `'${truncated.replace(/'/g, "\\'")}'`;
}

function fail(operation: string, reason: string, input: unknown): never {
  throw new Error(`${operation} failed: ${reason}. Got: ${formatInput(input)}`);
}

function parseOptionalInt(
  env: NodeJS.ProcessEnv,
  key: string,
  options: { min?: number; max?: number; allowZero?: boolean; defaultValue?: number } = {},
): number | undefined {
  const raw = env[key];
  if (raw === undefined || raw.trim().length === 0) {
    return options.defaultValue;
  }

  const value = Number(raw);
  if (!Number.isFinite(value) || !Number.isInteger(value)) {
    fail('parse env', `${key} must be an integer`, raw);
  }
  if (value === 0 && options.allowZero) {
    return 0;
  }
  if (options.min !== undefined && value < options.min) {
    fail('parse env', `${key} must be >= ${options.min}`, raw);
  }
  if (options.max !== undefined && value > options.max) {
    fail('parse env', `${key} must be <= ${options.max}`, raw);
  }

  return value;
}

function parseDocsUrl(env: NodeJS.ProcessEnv): string {
  const raw = env.DOCS_URL?.trim();
  const candidate = raw && raw.length > 0 ? raw : DEFAULT_DOCS_URL;

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    fail('parse env', 'DOCS_URL must be a valid URL', candidate);
  }

  if (parsed.protocol !== 'https:') {
    fail('parse env', 'DOCS_URL must use https', candidate);
  }

  return parsed.toString();
}

function validateCachePath(env: NodeJS.ProcessEnv): void {
  const raw = env.CACHE_PATH;
  if (!raw || raw.trim().length === 0) return;
  const trimmed = raw.trim();

  if (trimmed.endsWith(path.sep)) {
    fail('parse env', 'CACHE_PATH must include a filename, not a directory', raw);
  }
}

/**
 * Validate all runtime environment variables used by this server.
 * The server fails fast on invalid values instead of silently falling back.
 */
export function loadConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  const docsUrl = parseDocsUrl(env);
  const retryIntervalMs = parseOptionalInt(env, 'RETRY_INTERVAL_MS', {
    min: MIN_RETRY_INTERVAL_MS,
    max: MAX_RETRY_INTERVAL_MS,
    defaultValue: DEFAULT_RETRY_INTERVAL_MS,
  }) ?? DEFAULT_RETRY_INTERVAL_MS;

  // Validate additional env vars consumed in lower layers.
  parseOptionalInt(env, 'CACHE_TTL_MS', { min: 0 });
  parseOptionalInt(env, 'DOCS_CACHE_MAX_STALE_MS', { min: 0 });
  parseOptionalInt(env, 'MIN_SECTION_COUNT', { min: 0 });
  parseOptionalInt(env, 'MAX_INDEX_CACHE_BYTES', { min: 1 });
  parseOptionalInt(env, 'MAX_RESPONSE_BYTES', { min: 1 });
  parseOptionalInt(env, 'FETCH_TIMEOUT_MS', { min: 0 });
  validateCachePath(env);

  return {
    docsUrl,
    retryIntervalMs,
  };
}
