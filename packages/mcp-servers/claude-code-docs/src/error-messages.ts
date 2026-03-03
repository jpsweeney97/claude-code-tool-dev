export function formatSearchError(err: unknown): string {
  if (err instanceof Error) {
    const className = err.constructor.name;
    return `Search failed (ERR_SEARCH). [${className}] ${err.message}`;
  }
  return `Search failed (ERR_SEARCH). ${String(err)}`;
}
