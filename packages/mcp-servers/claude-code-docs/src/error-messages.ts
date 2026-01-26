export function formatSearchError(err: unknown): string {
  const message = err instanceof Error ? err.message : 'unknown';
  return `Search failed (ERR_SEARCH). ${message}`;
}
