import { describe, it, expect, vi } from 'vitest';

vi.mock('node:fs/promises', async (importOriginal) => {
  const actual = await importOriginal<typeof import('node:fs/promises')>();
  const mocked = {
    ...actual,
    unlink: vi.fn(actual.unlink),
    writeFile: vi.fn(actual.writeFile),
  };
  return { ...mocked, default: mocked };
});

describe('fs/promises mock sanity', () => {
  it('exposes mocked writeFile and unlink', async () => {
    const fsModule = await import('node:fs/promises');
    const fs = (fsModule as any).default ?? fsModule;
    expect(vi.isMockFunction(fs.writeFile)).toBe(true);
    expect(vi.isMockFunction(fs.unlink)).toBe(true);
  });
});
