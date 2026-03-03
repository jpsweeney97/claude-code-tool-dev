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

  it('includes class name for Error subclasses', () => {
    const message = formatSearchError(new TypeError('bad type'));
    expect(message).toContain('[TypeError]');
    expect(message).toContain('bad type');
  });

  it('includes class name for RangeError', () => {
    const message = formatSearchError(new RangeError('out of range'));
    expect(message).toContain('[RangeError]');
    expect(message).toContain('out of range');
  });

  it('includes class name for plain Error', () => {
    const message = formatSearchError(new Error('boom'));
    expect(message).toContain('[Error]');
  });

  it('uses String() for non-Error values', () => {
    const message = formatSearchError('oops');
    expect(message).toContain('ERR_SEARCH');
    expect(message).toContain('oops');
  });

  it('uses String() for numeric non-Error values', () => {
    const message = formatSearchError(42);
    expect(message).toContain('42');
  });

  it('uses String() for null', () => {
    const message = formatSearchError(null);
    expect(message).toContain('null');
  });
});
