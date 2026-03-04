// tests/integration.test.ts
//
// Integration test assessment (B13):
//
// Purpose: Validates that loadFromOfficial can fetch and parse live docs from
// code.claude.com, producing non-empty MarkdownFile[] with expected topics.
//
// Why skipped: Makes real HTTP requests to code.claude.com. Not suitable for
// CI (flaky on network issues, slow, depends on external service).
//
// API-shape bug (D7): The original test treated the return value of
// loadFromOfficial as an array, but the function returns { files, contentHash }.
// Fixed below — destructure .files before asserting.
//
// Unskip feasibility:
//   - Mock server approach: Viable but low value. The loader already has
//     thorough unit tests with fixtures (see loader.test.ts). A mock HTTP
//     server would duplicate that coverage without testing the real endpoint.
//   - Manual smoke test: Run with `INTEGRATION=1 vitest integration` when
//     needed to verify against live docs. The skip guard below supports this.
//   - Recommendation: Keep skipped in CI. The D7 fix ensures it works when
//     run manually. Cost of a full mock server outweighs benefit given
//     existing unit test coverage.
//
import { describe, it, expect } from 'vitest';
import { loadFromOfficial } from '../src/loader.js';

describe('integration: loadFromOfficial with real network', () => {
  it.skipIf(!process.env.INTEGRATION)('fetches real docs from code.claude.com', async () => {
    const { files } = await loadFromOfficial('https://code.claude.com/docs/llms-full.txt');

    expect(files.length).toBeGreaterThan(0);

    const hasHooks = files.some((f) => f.path.includes('hooks'));
    const hasSkills = files.some((f) => f.path.includes('skills'));
    const hasMcp = files.some((f) => f.path.includes('mcp'));

    expect(hasHooks || hasSkills || hasMcp).toBe(true);
  }, 60000);
});
