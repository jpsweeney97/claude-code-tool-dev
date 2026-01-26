import { describe, it, expect } from 'vitest';
import { formatSearchError } from '../src/error-messages.js';

describe('formatSearchError', () => {
  it('includes error code in message', () => {
    const message = formatSearchError(new Error('boom'));
    expect(message).toContain('ERR_SEARCH');
  });

  it('includes error message when available', () => {
    const message = formatSearchError(new Error('boom'));
    expect(message).toContain('boom');
  });

  it('handles non-Error values', () => {
    const message = formatSearchError('oops');
    expect(message).toContain('ERR_SEARCH');
  });
});
