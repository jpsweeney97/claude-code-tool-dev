# Code Review Audit Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 18 issues from the 2026-01-12 code review audit on the `feat/extension-docs-chunking-v2` branch.

**Architecture:** Three-phase approach—Critical fixes first (silent failures in Python hook), then Important fixes (error handling in both Python and TypeScript), then Suggestions (tests and improvements). Each phase verified independently before proceeding.

**Tech Stack:** Python 3.12 (dataclasses, subprocess), TypeScript (Vitest), Git

---

## Prerequisites

**Step 1: Switch to feature branch**

Run: `git checkout feat/extension-docs-chunking-v2`
Expected: `Switched to branch 'feat/extension-docs-chunking-v2'`

**Step 2: Verify clean working tree**

Run: `git status`
Expected: `nothing to commit, working tree clean`

---

## Task 1: Fix `log()` Silent Catch

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:64-73`
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing test**

```python
# Add to test_require_gitflow.py
def test_log_warns_on_write_failure(monkeypatch, capsys):
    """log() should warn once (not spam) when file write fails."""
    import require_gitflow
    require_gitflow._log_warning_shown = False
    require_gitflow.DEBUG = True

    def mock_open(*args, **kwargs):
        raise OSError("Disk full")

    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(require_gitflow.LOG_FILE.parent, "mkdir", lambda *a, **k: None)

    require_gitflow.log("INFO", "test message 1")
    require_gitflow.log("INFO", "test message 2")

    captured = capsys.readouterr()
    # Should warn once, not twice
    assert captured.err.count("Warning: Could not write to log file") == 1
    assert "Disk full" in captured.err
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_log_warns_on_write_failure -v`
Expected: FAIL (no `_log_warning_shown` attribute)

**Step 3: Write minimal implementation**

In `.claude/hooks/require-gitflow.py`, add before `log()` function:

```python
_log_warning_shown = False
```

Then modify the `log()` function exception handling (around line 72):

```python
def log(level: str, message: str) -> None:
    """Log message to stderr (if debug) and log file."""
    global _log_warning_shown
    if not DEBUG and level == "DEBUG":
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {message}"

    if DEBUG:
        print(f"[GITFLOW] {message}", file=sys.stderr)

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except PermissionError:
        pass  # Expected in sandboxed environments
    except OSError as e:
        if DEBUG and not _log_warning_shown:
            print(f"[GITFLOW] Warning: Could not write to log file: {e}", file=sys.stderr)
            _log_warning_shown = True
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_log_warns_on_write_failure -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(hooks): add deduped warning for log file write failures

- Add _log_warning_shown flag to prevent stderr spam
- Catch PermissionError silently (expected in sandboxes)
- Catch OSError and warn once in DEBUG mode

Addresses audit issue: silent failure in log() function"
```

---

## Task 2: Fix `resolve_git_dir()` Silent Catch

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:213-233`

**Step 1: Write the failing test**

```python
# Add to test_require_gitflow.py
def test_resolve_git_dir_logs_on_read_error(monkeypatch, tmp_path):
    """resolve_git_dir() should log when gitdir file is unreadable."""
    import require_gitflow
    require_gitflow.DEBUG = True
    logged_messages = []

    def mock_log(level, message):
        logged_messages.append((level, message))

    monkeypatch.setattr(require_gitflow, "log", mock_log)

    # Create a gitdir file that will fail to read
    git_file = tmp_path / ".git"
    git_file.write_bytes(b"\xff\xfe")  # Invalid UTF-8

    result = require_gitflow.resolve_git_dir(str(git_file))

    # Should return original path on error
    assert result == str(git_file)
    # Should have logged
    assert any("Could not resolve git dir" in msg for _, msg in logged_messages)
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_resolve_git_dir_logs_on_read_error -v`
Expected: FAIL (no log message produced)

**Step 3: Write minimal implementation**

Modify `resolve_git_dir()` in `.claude/hooks/require-gitflow.py`:

```python
def resolve_git_dir(git_dir: str) -> str:
    """
    Resolve git directory, following gitdir file indirection.

    In linked worktrees and some submodules, .git is a file containing:
        gitdir: /path/to/actual/.git/worktrees/name

    This function follows that indirection. On error, returns original path.
    """
    git_path = Path(git_dir)

    if git_path.is_file():
        try:
            content = git_path.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                pointed_path = content[7:].strip()
                if not os.path.isabs(pointed_path):
                    pointed_path = str(git_path.parent / pointed_path)
                resolved = os.path.normpath(pointed_path)
                log("DEBUG", f"Resolved gitdir indirection: {git_dir} -> {resolved}")
                return resolved
        except (OSError, UnicodeDecodeError) as e:
            log("DEBUG", f"Could not resolve git dir {git_dir!r}: {e}")

    return git_dir
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_resolve_git_dir_logs_on_read_error -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(hooks): log errors in resolve_git_dir instead of silent catch

- Catch specific exceptions (OSError, UnicodeDecodeError)
- Log errors at DEBUG level for troubleshooting
- Add explicit UTF-8 encoding to read_text()

Addresses audit issue: silent failure in resolve_git_dir()"
```

---

## Task 3: Fix `GitContext` Invalid States

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:235-242`

**Step 1: Write the failing test**

```python
# Add to test_require_gitflow.py
import pytest

def test_gitcontext_rejects_invalid_states():
    """GitContext should reject logically invalid states at construction."""
    from require_gitflow import GitContext

    # is_repo=False but other fields set
    with pytest.raises(ValueError, match="is_repo=False"):
        GitContext(is_repo=False, branch="main")

    with pytest.raises(ValueError, match="is_repo=False"):
        GitContext(is_repo=False, has_commits=True)

    # is_repo=True but no git_dir
    with pytest.raises(ValueError, match="git_dir is None"):
        GitContext(is_repo=True, git_dir=None)

    # is_detached without has_commits
    with pytest.raises(ValueError, match="is_detached=True requires has_commits"):
        GitContext(is_repo=True, git_dir="/path", is_detached=True, has_commits=False)

    # branch and is_detached both set
    with pytest.raises(ValueError, match="mutually exclusive"):
        GitContext(is_repo=True, git_dir="/path", branch="main", is_detached=True, has_commits=True)


def test_gitcontext_accepts_valid_states():
    """GitContext should accept valid states."""
    from require_gitflow import GitContext

    # Not a repo
    ctx = GitContext(is_repo=False)
    assert ctx.is_repo is False

    # Repo with branch
    ctx = GitContext(is_repo=True, git_dir="/path", branch="main", has_commits=True)
    assert ctx.branch == "main"

    # Repo with detached HEAD
    ctx = GitContext(is_repo=True, git_dir="/path", is_detached=True, has_commits=True)
    assert ctx.is_detached is True


def test_gitcontext_is_frozen():
    """GitContext should be immutable after construction."""
    from require_gitflow import GitContext

    ctx = GitContext(is_repo=True, git_dir="/path", branch="main", has_commits=True)

    with pytest.raises(AttributeError):
        ctx.branch = "other"
```

**Step 2: Run tests to verify they fail**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_gitcontext_rejects_invalid_states test_require_gitflow.py::test_gitcontext_accepts_valid_states test_require_gitflow.py::test_gitcontext_is_frozen -v`
Expected: FAIL (no validation, not frozen)

**Step 3: Write minimal implementation**

Replace `GitContext` in `.claude/hooks/require-gitflow.py`:

```python
@dataclass(frozen=True)
class GitContext:
    """
    Cached git repository context.

    Invariants:
    - is_repo=False implies all other fields are at defaults
    - is_repo=True implies git_dir is not None
    - branch and is_detached are mutually exclusive
    - is_detached requires has_commits=True
    """
    is_repo: bool = False
    has_commits: bool = False
    git_dir: Optional[str] = None
    branch: Optional[str] = None
    is_detached: bool = False

    def __post_init__(self) -> None:
        if not self.is_repo:
            if self.has_commits or self.git_dir or self.branch or self.is_detached:
                raise ValueError(
                    f"GitContext invariant violated: is_repo=False but other fields set: "
                    f"has_commits={self.has_commits}, git_dir={self.git_dir!r}, "
                    f"branch={self.branch!r}, is_detached={self.is_detached}"
                )
        elif self.git_dir is None:
            raise ValueError("GitContext invariant violated: is_repo=True but git_dir is None")
        if self.is_detached and not self.has_commits:
            raise ValueError("GitContext invariant violated: is_detached=True requires has_commits=True")
        if self.branch is not None and self.is_detached:
            raise ValueError("GitContext invariant violated: branch and is_detached are mutually exclusive")
```

**Step 4: Run tests to verify they pass**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_gitcontext_rejects_invalid_states test_require_gitflow.py::test_gitcontext_accepts_valid_states test_require_gitflow.py::test_gitcontext_is_frozen -v`
Expected: PASS

**Step 5: Review all GitContext instantiations**

Run: `rg "GitContext\(" .claude/hooks/require-gitflow.py`
Verify each instantiation passes new validation rules.

**Step 6: Run full test suite to catch any broken instantiations**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(hooks): make GitContext frozen with invariant validation

- Add frozen=True to prevent post-construction mutation
- Add __post_init__ validation for state invariants
- Reject invalid states at construction time

Addresses audit issue: GitContext allows invalid states"
```

---

## Task 4: Fix `main()` Broad Exception Catch

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:390-394`

**Step 1: Write the failing test**

```python
# Add to test_require_gitflow.py
def test_main_exception_includes_context(monkeypatch, capsys):
    """main() should include exception type and tool context in error messages."""
    import json
    import require_gitflow

    # Simulate input that will cause an error after parsing
    test_input = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "test"}
    })

    def mock_stdin_read():
        return test_input

    def mock_process(*args, **kwargs):
        raise RuntimeError("Simulated error")

    monkeypatch.setattr("sys.stdin.read", mock_stdin_read)
    monkeypatch.setattr(require_gitflow, "process_tool_call", mock_process)

    with pytest.raises(SystemExit) as exc_info:
        require_gitflow.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "RuntimeError" in captured.err
    assert "tool=Bash" in captured.err or "Bash" in captured.err
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_main_exception_includes_context -v`
Expected: FAIL (error message lacks context)

**Step 3: Write minimal implementation**

Modify the exception handling at the end of `main()`:

```python
    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        raise  # Let these propagate with their exit codes
    except Exception as e:
        import traceback
        tool_info = f"tool={data.get('tool_name', 'unknown')}" if 'data' in dir() else "before parsing"
        log("ERROR", f"Unexpected error ({tool_info}): {type(e).__name__}: {e}")
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print(f"Hook error ({tool_info}): {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py::test_main_exception_includes_context -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(hooks): improve main() exception handling with context

- Re-raise KeyboardInterrupt and SystemExit
- Include exception type in error message
- Include tool name context when available
- Show traceback in DEBUG mode

Addresses audit issue: broad exception catch with minimal context"
```

---

## Task 5: Run Phase 1 Verification

**Step 1: Run all Python hook tests**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py -v`
Expected: All tests PASS

**Step 2: Test hook manually**

Run: `echo '{"tool_name":"Bash","tool_input":{"command":"echo test"}}' | python .claude/hooks/require-gitflow.py`
Expected: Hook executes without error (JSON output or no output)

**Step 3: Commit checkpoint**

```bash
git add -A
git commit --allow-empty -m "chore: Phase 1 complete - all Python hook critical fixes verified"
```

---

## Task 6: Fix `chunkFile()` Error Handling (TypeScript)

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/chunker.ts:16-28`
- Test: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Write the failing test**

```typescript
// Add to chunker.test.ts
describe('chunkFile error handling', () => {
  it('throws with file context on parse error', () => {
    // Malformed content that will cause an error
    const file: MarkdownFile = {
      path: 'test/malformed.md',
      content: null as unknown as string,  // Force invalid input
    };

    expect(() => chunkFile(file)).toThrow('test/malformed.md');
  });

  it('throws on missing path', () => {
    const file: MarkdownFile = {
      path: '',
      content: '# Test',
    };

    expect(() => chunkFile(file)).toThrow('file.path is required');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run chunker.test.ts -t "error handling"`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `chunkFile()` in `packages/mcp-servers/extension-docs/src/chunker.ts`:

```typescript
export function chunkFile(file: MarkdownFile): Chunk[] {
  // Input validation
  if (!file.path) {
    throw new Error('chunkFile: file.path is required');
  }
  if (file.content === undefined || file.content === null) {
    throw new Error(`chunkFile: file.content is required for ${file.path}`);
  }

  try {
    const { frontmatter, body } = parseFrontmatter(file.content, file.path);
    const metadataHeader = formatMetadataHeader(frontmatter);
    const preparedContent = metadataHeader + body;

    if (isSmallEnoughForWholeFile(preparedContent)) {
      return [createWholeFileChunk(file, preparedContent, frontmatter)];
    }

    const rawChunks = splitAtH2(file, preparedContent, frontmatter);
    return mergeSmallChunks(rawChunks, frontmatter);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to chunk file ${file.path}: ${message}`);
  }
}
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run chunker.test.ts -t "error handling"`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "fix(extension-docs): add error handling to chunkFile with file context

- Validate file.path and file.content at entry
- Wrap processing in try-catch
- Include file path in all error messages

Addresses audit issue: no error handling in chunkFile()"
```

---

## Task 7: Fix `FenceTracker` Regex Safety

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/fence-tracker.ts:23-27`
- Test: `packages/mcp-servers/extension-docs/tests/fence-tracker.test.ts`

**Step 1: Write the failing test**

```typescript
// Add to fence-tracker.test.ts
describe('FenceTracker edge cases', () => {
  it('handles empty fencePattern gracefully', () => {
    const tracker = new FenceTracker();

    // Force invalid internal state (for robustness testing)
    (tracker as any).inFence = true;
    (tracker as any).fencePattern = '';

    // Should not throw SyntaxError from invalid regex
    expect(() => tracker.processLine('```')).not.toThrow();
  });

  it('handles nested fence documentation pattern', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('````markdown')).toBe(true);
    expect(tracker.processLine('Here is an example:')).toBe(true);
    expect(tracker.processLine('```python')).toBe(true);  // Inside, NOT a new fence
    expect(tracker.processLine('print("hello")')).toBe(true);
    expect(tracker.processLine('```')).toBe(true);  // Still inside outer
    expect(tracker.processLine('````')).toBe(false);  // Now closed
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run fence-tracker.test.ts -t "edge cases"`
Expected: FAIL (empty pattern causes regex error)

**Step 3: Write minimal implementation**

Modify `processLine()` in `packages/mcp-servers/extension-docs/src/fence-tracker.ts`:

```typescript
export class FenceTracker {
  private inFence = false;
  private fencePattern: string | null = null;

  processLine(line: string): boolean {
    const fence = line.match(/^( {0,3})(`{3,}|~{3,})/);
    if (fence) {
      if (!this.inFence) {
        this.inFence = true;
        this.fencePattern = fence[2];
      } else if (this.fencePattern && this.fencePattern.length > 0) {
        const closeRegex = new RegExp(
          `^ {0,3}${this.fencePattern[0]}{${this.fencePattern.length},}\\s*$`
        );
        if (closeRegex.test(line)) {
          this.inFence = false;
          this.fencePattern = null;
        }
      }
    }
    return this.inFence;
  }

  get isInFence(): boolean {
    return this.inFence;
  }

  reset(): void {
    this.inFence = false;
    this.fencePattern = null;
  }
}
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run fence-tracker.test.ts -t "edge cases"`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/fence-tracker.ts packages/mcp-servers/extension-docs/tests/fence-tracker.test.ts
git commit -m "fix(extension-docs): guard FenceTracker against empty pattern

- Change fencePattern type from string to string | null
- Add length check before regex construction
- Add nested fence documentation test

Addresses audit issues: regex safety, null sentinel, nested fence test"
```

---

## Task 8: Fix Global Mutable State in frontmatter.ts

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/frontmatter.ts`
- Modify: `packages/mcp-servers/extension-docs/src/chunker.ts` (update import)
- Test: `packages/mcp-servers/extension-docs/tests/frontmatter.test.ts`

**Step 1: Write the failing test**

```typescript
// Add to frontmatter.test.ts
describe('parseFrontmatter warnings', () => {
  it('returns warnings in result instead of global state', () => {
    const content = '---\ncategory: [invalid]\n---\nBody';
    const { warnings } = parseFrontmatter(content, 'test.md');

    expect(warnings).toBeDefined();
    expect(Array.isArray(warnings)).toBe(true);
  });

  it('isolates warnings between calls', () => {
    // First call with invalid content
    const { warnings: w1 } = parseFrontmatter('---\ncategory: [x]\n---\n', 'a.md');

    // Second call with valid content
    const { warnings: w2 } = parseFrontmatter('---\ncategory: valid\n---\n', 'b.md');

    // Second call should have no warnings (isolated)
    expect(w2.length).toBe(0);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run frontmatter.test.ts -t "warnings"`
Expected: FAIL (warnings not in return type)

**Step 3: Write minimal implementation**

Modify `parseFrontmatter()` return type and implementation:

```typescript
export interface ParseResult {
  frontmatter: Frontmatter;
  body: string;
  warnings: ParseWarning[];
}

export function parseFrontmatter(
  content: string,
  filePath: string
): ParseResult {
  const warnings: ParseWarning[] = [];  // Local, not global

  // ... existing parsing logic, change parseWarnings.push to warnings.push ...

  return { frontmatter, body, warnings };
}

// Keep deprecated global functions for backward compatibility
const parseWarnings: ParseWarning[] = [];

/** @deprecated Use warnings returned from parseFrontmatter() */
export function getParseWarnings(): ParseWarning[] {
  return [...parseWarnings];
}

/** @deprecated Use warnings returned from parseFrontmatter() */
export function clearParseWarnings(): void {
  parseWarnings.length = 0;
}
```

**Step 4: Update chunker.ts to use new return type**

```typescript
// In chunkFile():
const { frontmatter, body, warnings } = parseFrontmatter(file.content, file.path);

if (warnings.length > 0) {
  console.warn(`[chunker] Warnings for ${file.path}:`, warnings);
}
```

**Step 5: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run frontmatter.test.ts -t "warnings"`
Expected: PASS

**Step 6: Run full test suite**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/frontmatter.ts packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/frontmatter.test.ts
git commit -m "fix(extension-docs): return warnings from parseFrontmatter instead of global

- Add warnings to return type
- Use local array instead of module-level global
- Surface warnings in chunkFile via console.warn
- Keep deprecated global functions for compatibility

Addresses audit issue: global mutable state for warnings"
```

---

## Task 9: Add Table Bounds Check

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/chunker.ts` (splitOversizedTable)
- Test: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Write the failing test**

```typescript
// Add to chunker.test.ts
describe('table handling', () => {
  it('handles malformed table without separator', () => {
    const content = [
      '# Title',
      '## Section',
      '| A | B |',
      '| 1 | 2 |',  // This is data, not separator
      '| 3 | 4 |',
      '',
      'After table.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/bad-table.md', content };
    const chunks = chunkFile(file);

    // Should not crash, should preserve content
    expect(chunks.length).toBeGreaterThan(0);
    const allContent = chunks.map(c => c.content).join('');
    expect(allContent).toContain('| A | B |');
  });

  it('handles empty table (header + separator only)', () => {
    const content = [
      '# Title',
      '## Section',
      '| A | B |',
      '|---|---|',
      '',
      'After table.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/empty-table.md', content };
    const chunks = chunkFile(file);

    expect(chunks.length).toBeGreaterThan(0);
    const allContent = chunks.map(c => c.content).join('');
    expect(allContent).toContain('| A | B |');
  });
});
```

**Step 2: Run test to verify behavior**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run chunker.test.ts -t "table handling"`
Expected: May pass or fail depending on current implementation

**Step 3: Add separator validation to splitOversizedTable**

```typescript
function splitOversizedTable(tableLines: string[]): string[] {
  if (tableLines.length < 3) {
    return [tableLines.join('\n')];
  }

  // Validate table structure: second line should be separator
  const separator = tableLines[1];
  if (!/^\s*\|[\s\-:|]+\|\s*$/.test(separator)) {
    // Not a valid markdown table - return as-is
    return [tableLines.join('\n')];
  }

  const headerLines = tableLines.slice(0, 2);
  const dataRows = tableLines.slice(2);
  // ... rest of implementation
}
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run chunker.test.ts -t "table handling"`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "fix(extension-docs): add bounds check for malformed tables

- Validate separator line before treating as table
- Handle tables without proper separator gracefully
- Add tests for malformed and empty tables

Addresses audit issue: no bounds check for malformed tables"
```

---

## Task 10: Add Remaining Test Coverage

**Files:**
- Test: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Add intro-only oversized test**

```typescript
it('handles intro-only oversized files (no H2 headings)', () => {
  const content = [
    '---',
    'category: test',
    '---',
    '# Title Only',
    ...Array(200).fill('Very long intro paragraph content line that fills the file.'),
  ].join('\n');

  const file: MarkdownFile = { path: 'test/no-h2.md', content };
  const chunks = chunkFile(file);

  expect(chunks.length).toBeGreaterThan(1);
  for (const chunk of chunks) {
    expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
  }
});
```

**Step 2: Add overlap accumulation test**

```typescript
it('does not excessively duplicate content via overlap', () => {
  const longParagraph = Array(60).fill('word').join(' ');
  const manyParagraphs = Array(50).fill(longParagraph).join('\n\n');

  const content = [
    '# Title',
    '## Section',
    manyParagraphs,
  ].join('\n');

  const file: MarkdownFile = { path: 'test/overlap.md', content };
  const chunks = chunkFile(file);

  const allContent = chunks.map(c => c.content).join('|||');
  const wordCount = (allContent.match(/word/g) || []).length;
  const expectedMax = 50 * 60 * 1.3;  // Original + 30% for overlap
  expect(wordCount).toBeLessThan(expectedMax);
});
```

**Step 3: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run chunker.test.ts`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "test(extension-docs): add edge case tests for chunker

- Add test for intro-only oversized files
- Add test for overlap accumulation bounds

Addresses audit issues: missing splitBounded tests"
```

---

## Task 11: Fix corpus-validation.test.ts Path Handling

**Files:**
- Modify: `packages/mcp-servers/extension-docs/tests/corpus-validation.test.ts`

**Step 1: Add skip condition with warning**

```typescript
import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS_PATH = process.env.DOCS_PATH ?? resolve(__dirname, '../../../../docs/extension-reference');
const docsExist = existsSync(DOCS_PATH);

describe.skipIf(!docsExist)('corpus validation', () => {
  // Log skip reason at module level
  if (!docsExist) {
    console.warn(
      `SKIPPING corpus validation: DOCS_PATH not found at ${DOCS_PATH}\n` +
      `Set DOCS_PATH environment variable to run this test.`
    );
  }

  it('all chunks within size bounds', () => {
    // ... existing test
  });
});
```

**Step 2: Run test to verify skip behavior**

Run: `cd packages/mcp-servers/extension-docs && npm test -- --run corpus-validation.test.ts`
Expected: Test skipped with warning (or passes if docs exist)

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/corpus-validation.test.ts
git commit -m "fix(extension-docs): skip corpus validation when path missing

- Use describe.skipIf to conditionally skip
- Log warning explaining how to enable test

Addresses audit issue: external path dependency"
```

---

## Task 12: Fix `run_git()` Timeout vs Not-Found (Python)

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:199-211`

**Step 1: Modify exception handling**

```python
def run_git(*args: str) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        log("DEBUG", f"Git command timed out: git {' '.join(args)}")
        return False, ""
    except FileNotFoundError:
        log("DEBUG", "Git not found in PATH")
        return False, ""
```

**Step 2: Run existing tests**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add .claude/hooks/require-gitflow.py
git commit -m "fix(hooks): distinguish timeout from git-not-found in run_git

- Separate exception handlers for TimeoutExpired and FileNotFoundError
- Log different messages for debugging

Addresses audit issue: timeout indistinguishable from git not found"
```

---

## Task 13: Document `related_to` Naming Choice

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/frontmatter.ts`

**Step 1: Add comment**

```typescript
export interface Frontmatter {
  category?: string;
  tags?: string[];
  topic?: string;
  id?: string;
  requires?: string[];
  /**
   * Related document IDs.
   * Note: Uses snake_case to match YAML frontmatter field names.
   */
  related_to?: string[];
}
```

**Step 2: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/frontmatter.ts
git commit -m "docs(extension-docs): document related_to naming choice

Addresses audit issue: inconsistent naming convention"
```

---

## Task 14: Final Verification

**Step 1: Run all Python tests**

Run: `cd .claude/hooks && uv run pytest test_require_gitflow.py -v`
Expected: All tests PASS

**Step 2: Run all TypeScript tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: All tests PASS

**Step 3: Build TypeScript**

Run: `cd packages/mcp-servers/extension-docs && npm run build`
Expected: Build succeeds

**Step 4: Final commit**

```bash
git add -A
git commit --allow-empty -m "chore: complete code review audit remediation

All 18 issues addressed:
- 3 Critical: silent failures fixed, GitContext validated
- 7 Important: error handling improved, tests added
- 8 Suggestions: tests, documentation, edge cases

Branch ready for merge review."
```

---

## Summary

| Task | Issue | Type |
|------|-------|------|
| 1 | log() silent catch | Critical |
| 2 | resolve_git_dir() silent catch | Critical |
| 3 | GitContext invalid states | Critical |
| 4 | main() broad exception | Important |
| 5 | Phase 1 verification | Checkpoint |
| 6 | chunkFile() error handling | Important |
| 7 | FenceTracker regex safety | Important |
| 8 | frontmatter global state | Important |
| 9 | Table bounds check | Suggestion |
| 10 | Missing tests | Important |
| 11 | corpus-validation path | Suggestion |
| 12 | run_git timeout vs not-found | Suggestion |
| 13 | related_to naming | Suggestion |
| 14 | Final verification | Checkpoint |
