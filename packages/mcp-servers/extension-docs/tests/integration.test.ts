// tests/integration.test.ts
import { describe, it, expect } from 'vitest';
import { loadFromOfficial } from '../src/loader.js';

describe('integration: loadFromOfficial with real network', () => {
  it.skip('fetches real docs from code.claude.com', async () => {
    const files = await loadFromOfficial('https://code.claude.com/docs/llms-full.txt');

    expect(files.length).toBeGreaterThan(0);

    const hasHooks = files.some((f) => f.path.includes('hooks'));
    const hasSkills = files.some((f) => f.path.includes('skills'));
    const hasMcp = files.some((f) => f.path.includes('mcp'));

    expect(hasHooks || hasSkills || hasMcp).toBe(true);
  }, 60000);
});
