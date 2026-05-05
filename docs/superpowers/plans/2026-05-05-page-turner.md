# Page Turner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Mac browser extension (Chrome + Firefox MV3) that navigates paginated websites via `Ctrl+Shift+Arrow` keyboard shortcut.

**Architecture:** Two-file extension using the Commands API. Background script listens for shortcut commands and injects a self-contained navigation function into the active tab via `scripting.executeScript`. Pattern registry inside the injected function detects page numbers in URLs and navigates.

**Tech Stack:** Vanilla JavaScript, Manifest V3, WebExtensions APIs (commands, scripting, tabs)

**Spec:** `docs/superpowers/specs/2026-05-05-page-turner-design.md`

---

### Task 1: Project Scaffold and Manifest

**Files:**
- Create: `page-turner/manifest.json`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p /Users/jp/Projects/active/claude-code-tool-dev/page-turner
```

- [ ] **Step 2: Write manifest.json**

```json
{
  "manifest_version": 3,
  "name": "Page Turner",
  "version": "1.0",
  "description": "Navigate paginated sites with a keyboard shortcut",
  "commands": {
    "next-page": {
      "suggested_key": { "mac": "MacCtrl+Shift+Right" },
      "description": "Go to next page"
    },
    "prev-page": {
      "suggested_key": { "mac": "MacCtrl+Shift+Left" },
      "description": "Go to previous page"
    }
  },
  "background": {
    "scripts": ["background.js"],
    "service_worker": "background.js"
  },
  "permissions": ["activeTab", "scripting"]
}
```

- [ ] **Step 3: Commit**

```bash
git add page-turner/manifest.json
git commit -m "feat(page-turner): add MV3 manifest with commands and permissions"
```

---

### Task 2: Pattern Registry — `query-page` Pattern

The pattern registry lives inside the `navigatePage` function (Task 5), but we build and test each pattern independently first using a test harness, then assemble them.

**Files:**
- Create: `page-turner/test-patterns.html` (manual test harness)
- Create: `page-turner/patterns.js` (standalone patterns module for testing — will be inlined into background.js in Task 5)

- [ ] **Step 1: Write the pattern module**

Create `page-turner/patterns.js` with a `parsePageNumber` helper and the `query-page` pattern:

```javascript
function parsePageNumber(value) {
  const result = parseInt(value, 10);
  if (isNaN(result) || result.toString() !== value || result < 0) return null;
  return result;
}

const PATTERNS = [
  {
    name: "query-page",
    match(url) {
      const params = new URLSearchParams(url.search);
      for (const key of ["page", "p", "pg"]) {
        const raw = params.get(key);
        if (raw === null) continue;
        const value = parsePageNumber(raw);
        if (value === null) continue;
        return {
          value,
          min: 1,
          build(n) {
            const newUrl = new URL(url.href);
            const newParams = new URLSearchParams(newUrl.search);
            newParams.set(key, n.toString());
            newUrl.search = newParams.toString();
            return newUrl.href;
          },
        };
      }
      return null;
    },
  },
];
```

- [ ] **Step 2: Write the test harness**

Create `page-turner/test-patterns.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Pattern Tests</title></head>
<body>
<pre id="output"></pre>
<script>
function parsePageNumber(value) {
  const result = parseInt(value, 10);
  if (isNaN(result) || result.toString() !== value || result < 0) return null;
  return result;
}

const PATTERNS = [
  {
    name: "query-page",
    match(url) {
      const params = new URLSearchParams(url.search);
      for (const key of ["page", "p", "pg"]) {
        const raw = params.get(key);
        if (raw === null) continue;
        const value = parsePageNumber(raw);
        if (value === null) continue;
        return {
          value,
          min: 1,
          build(n) {
            const newUrl = new URL(url.href);
            const newParams = new URLSearchParams(newUrl.search);
            newParams.set(key, n.toString());
            newUrl.search = newParams.toString();
            return newUrl.href;
          },
        };
      }
      return null;
    },
  },
];

const out = document.getElementById("output");
let passed = 0;
let failed = 0;

function assert(label, actual, expected) {
  if (actual === expected) {
    out.textContent += `PASS: ${label}\n`;
    passed++;
  } else {
    out.textContent += `FAIL: ${label}\n  expected: ${expected}\n  actual:   ${actual}\n`;
    failed++;
  }
}

function testUrl(href) {
  return new URL(href);
}

// query-page: ?page=N
const qp1 = PATTERNS[0].match(testUrl("https://example.com/search?page=4&q=test"));
assert("query-page: ?page=4 value", qp1.value, 4);
assert("query-page: ?page=4 min", qp1.min, 1);
assert("query-page: ?page=4 build(5)", qp1.build(5), "https://example.com/search?page=5&q=test");
assert("query-page: ?page=4 build(3)", qp1.build(3), "https://example.com/search?page=3&q=test");

// query-page: ?p=N
const qp2 = PATTERNS[0].match(testUrl("https://example.com/?p=2"));
assert("query-page: ?p=2 value", qp2.value, 2);
assert("query-page: ?p=2 build(3)", qp2.build(3), "https://example.com/?p=3");

// query-page: ?pg=N
const qp3 = PATTERNS[0].match(testUrl("https://example.com/list?pg=10"));
assert("query-page: ?pg=10 value", qp3.value, 10);

// query-page: preserves hash
const qp4 = PATTERNS[0].match(testUrl("https://example.com/?page=1#section"));
assert("query-page: preserves hash", qp4.build(2), "https://example.com/?page=2#section");

// query-page: ?page=0 (below min but valid number — accepted, navigation flow handles floor)
const qp5 = PATTERNS[0].match(testUrl("https://example.com/?page=0"));
assert("query-page: ?page=0 value", qp5.value, 0);

// Negative cases
assert("query-page: no match on plain URL", PATTERNS[0].match(testUrl("https://example.com/")), null);
assert("query-page: no match on ?page=abc", PATTERNS[0].match(testUrl("https://example.com/?page=abc")), null);
assert("query-page: no match on ?page=01", PATTERNS[0].match(testUrl("https://example.com/?page=01")), null);
assert("query-page: no match on ?page=1.5", PATTERNS[0].match(testUrl("https://example.com/?page=1.5")), null);
assert("query-page: no match on ?page=1abc", PATTERNS[0].match(testUrl("https://example.com/?page=1abc")), null);
assert("query-page: no match on ?page=-1", PATTERNS[0].match(testUrl("https://example.com/?page=-1")), null);

// Duplicate params: first occurrence wins
const qp6 = PATTERNS[0].match(testUrl("https://example.com/?page=3&page=7"));
assert("query-page: duplicate params, first wins", qp6.value, 3);

out.textContent += `\n${passed} passed, ${failed} failed\n`;
</script>
</body>
</html>
```

- [ ] **Step 3: Open test harness in browser and verify all pass**

```bash
open /Users/jp/Projects/active/claude-code-tool-dev/page-turner/test-patterns.html
```

Expected: All tests show PASS, 0 failed.

- [ ] **Step 4: Commit**

```bash
git add page-turner/patterns.js page-turner/test-patterns.html
git commit -m "feat(page-turner): add query-page pattern with test harness"
```

---

### Task 3: Pattern Registry — Path Patterns

**Files:**
- Modify: `page-turner/patterns.js`
- Modify: `page-turner/test-patterns.html`

- [ ] **Step 1: Add path-page-slash and path-page-hyphen patterns to patterns.js**

Append to the `PATTERNS` array in `page-turner/patterns.js`:

```javascript
  {
    name: "path-page-slash",
    match(url) {
      const regex = /\/page\/(\d+)(?=\/|$)/;
      const m = url.pathname.match(regex);
      if (!m) return null;
      const value = parsePageNumber(m[1]);
      if (value === null) return null;
      return {
        value,
        min: 1,
        build(n) {
          const newPathname = url.pathname.replace(regex, `/page/${n}`);
          const newUrl = new URL(url.href);
          newUrl.pathname = newPathname;
          return newUrl.href;
        },
      };
    },
  },
  {
    name: "path-page-hyphen",
    match(url) {
      const regex = /\/page-(\d+)(?=\/|$)/;
      const m = url.pathname.match(regex);
      if (!m) return null;
      const value = parsePageNumber(m[1]);
      if (value === null) return null;
      return {
        value,
        min: 1,
        build(n) {
          const newPathname = url.pathname.replace(regex, `/page-${n}`);
          const newUrl = new URL(url.href);
          newUrl.pathname = newPathname;
          return newUrl.href;
        },
      };
    },
  },
```

- [ ] **Step 2: Add path pattern tests to test-patterns.html**

Add these test blocks after the query-page tests, before the summary line. Also add the two new pattern definitions to the inline `PATTERNS` array in the script (copy from patterns.js).

```javascript
// path-page-slash: /page/N
const ps1 = PATTERNS[1].match(testUrl("https://example.com/results/page/3"));
assert("path-page-slash: /page/3 value", ps1.value, 3);
assert("path-page-slash: /page/3 build(4)", ps1.build(4), "https://example.com/results/page/4");

// path-page-slash: /page/N/ (trailing slash)
const ps2 = PATTERNS[1].match(testUrl("https://example.com/page/5/"));
assert("path-page-slash: /page/5/ value", ps2.value, 5);
assert("path-page-slash: /page/5/ build(6)", ps2.build(6), "https://example.com/page/6/");

// path-page-slash: /page/N/foo (trailing segments preserved)
const ps3 = PATTERNS[1].match(testUrl("https://example.com/page/2/details"));
assert("path-page-slash: /page/2/details value", ps3.value, 2);
assert("path-page-slash: /page/2/details build(3)", ps3.build(3), "https://example.com/page/3/details");

// path-page-slash: preserves query and hash
const ps4 = PATTERNS[1].match(testUrl("https://example.com/page/1?sort=new#top"));
assert("path-page-slash: preserves query+hash", ps4.build(2), "https://example.com/page/2?sort=new#top");

// path-page-slash: negative cases
assert("path-page-slash: no match /xpage/3", PATTERNS[1].match(testUrl("https://example.com/xpage/3")), null);
assert("path-page-slash: no match /page/3a", PATTERNS[1].match(testUrl("https://example.com/page/3a")), null);
assert("path-page-slash: no match /page/", PATTERNS[1].match(testUrl("https://example.com/page/")), null);

// path-page-hyphen: /page-N
const ph1 = PATTERNS[2].match(testUrl("https://example.com/results/page-3"));
assert("path-page-hyphen: /page-3 value", ph1.value, 3);
assert("path-page-hyphen: /page-3 build(4)", ph1.build(4), "https://example.com/results/page-4");

// path-page-hyphen: /page-N/ (trailing slash)
const ph2 = PATTERNS[2].match(testUrl("https://example.com/page-5/"));
assert("path-page-hyphen: /page-5/ value", ph2.value, 5);
assert("path-page-hyphen: /page-5/ build(6)", ph2.build(6), "https://example.com/page-6/");

// path-page-hyphen: preserves trailing segments
const ph3 = PATTERNS[2].match(testUrl("https://example.com/page-2/details"));
assert("path-page-hyphen: /page-2/details build(3)", ph3.build(3), "https://example.com/page-3/details");

// path-page-hyphen: negative cases
assert("path-page-hyphen: no match /xpage-3", PATTERNS[2].match(testUrl("https://example.com/xpage-3")), null);
assert("path-page-hyphen: no match /page-3a", PATTERNS[2].match(testUrl("https://example.com/page-3a")), null);

// Pattern priority: ?page=N wins over /page/N
const priority = testUrl("https://example.com/page/2?page=5");
const priorityMatch = PATTERNS.find((p) => p.match(priority) !== null);
assert("priority: query-page wins over path-page-slash", priorityMatch.name, "query-page");
```

- [ ] **Step 3: Open test harness and verify all pass**

```bash
open /Users/jp/Projects/active/claude-code-tool-dev/page-turner/test-patterns.html
```

Expected: All tests PASS, 0 failed.

- [ ] **Step 4: Commit**

```bash
git add page-turner/patterns.js page-turner/test-patterns.html
git commit -m "feat(page-turner): add path-page-slash and path-page-hyphen patterns"
```

---

### Task 4: Interactive Element Guard

**Files:**
- Modify: `page-turner/test-patterns.html` (add guard tests)

- [ ] **Step 1: Write the isInteractiveElement function**

This will live inside `navigatePage` in the final assembly. Define it here for testing:

```javascript
function isInteractiveElement(el) {
  if (!el) return false;

  const tag = el.tagName;

  if (tag === "TEXTAREA" || tag === "SELECT" || tag === "VIDEO" ||
      tag === "AUDIO" || tag === "IFRAME" || tag === "FRAME") {
    return true;
  }

  if (tag === "INPUT") {
    const type = (el.type || "text").toLowerCase();
    const interactiveTypes = new Set([
      "text", "search", "number", "email", "url", "tel", "password",
      "range", "date", "time", "datetime-local", "month", "week", "color",
    ]);
    return interactiveTypes.has(type);
  }

  if (el.isContentEditable) return true;

  const role = (el.getAttribute("role") || "").toLowerCase();
  const interactiveRoles = new Set([
    "textbox", "slider", "listbox", "menu", "menubar",
    "tree", "treegrid", "grid", "combobox", "spinbutton", "tablist",
  ]);
  if (interactiveRoles.has(role)) return true;

  return false;
}
```

- [ ] **Step 2: Add guard tests to test-patterns.html**

Add a section that creates DOM elements and tests the guard:

```javascript
// Interactive element guard tests
function makeEl(tag, attrs) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    el.setAttribute(k, v);
  }
  return el;
}

assert("guard: input[text]", isInteractiveElement(makeEl("input", { type: "text" })), true);
assert("guard: input[search]", isInteractiveElement(makeEl("input", { type: "search" })), true);
assert("guard: input[number]", isInteractiveElement(makeEl("input", { type: "number" })), true);
assert("guard: input[range]", isInteractiveElement(makeEl("input", { type: "range" })), true);
assert("guard: input[date]", isInteractiveElement(makeEl("input", { type: "date" })), true);
assert("guard: input[color]", isInteractiveElement(makeEl("input", { type: "color" })), true);
assert("guard: input[password]", isInteractiveElement(makeEl("input", { type: "password" })), true);
assert("guard: input[no type] (defaults to text)", isInteractiveElement(makeEl("input")), true);
assert("guard: input[checkbox]", isInteractiveElement(makeEl("input", { type: "checkbox" })), false);
assert("guard: input[submit]", isInteractiveElement(makeEl("input", { type: "submit" })), false);
assert("guard: input[hidden]", isInteractiveElement(makeEl("input", { type: "hidden" })), false);
assert("guard: textarea", isInteractiveElement(makeEl("textarea")), true);
assert("guard: select", isInteractiveElement(makeEl("select")), true);
assert("guard: video", isInteractiveElement(makeEl("video")), true);
assert("guard: audio", isInteractiveElement(makeEl("audio")), true);
assert("guard: iframe", isInteractiveElement(makeEl("iframe")), true);
assert("guard: div", isInteractiveElement(makeEl("div")), false);
assert("guard: a", isInteractiveElement(makeEl("a")), false);
assert("guard: button", isInteractiveElement(makeEl("button")), false);
assert("guard: null", isInteractiveElement(null), false);

// contentEditable
const editable = makeEl("div");
editable.contentEditable = "true";
assert("guard: contenteditable div", isInteractiveElement(editable), true);

// ARIA roles
assert("guard: role=textbox", isInteractiveElement(makeEl("div", { role: "textbox" })), true);
assert("guard: role=slider", isInteractiveElement(makeEl("div", { role: "slider" })), true);
assert("guard: role=listbox", isInteractiveElement(makeEl("div", { role: "listbox" })), true);
assert("guard: role=menu", isInteractiveElement(makeEl("div", { role: "menu" })), true);
assert("guard: role=grid", isInteractiveElement(makeEl("div", { role: "grid" })), true);
assert("guard: role=combobox", isInteractiveElement(makeEl("div", { role: "combobox" })), true);
assert("guard: role=tablist", isInteractiveElement(makeEl("div", { role: "tablist" })), true);
assert("guard: role=button", isInteractiveElement(makeEl("div", { role: "button" })), false);
assert("guard: role=navigation", isInteractiveElement(makeEl("div", { role: "navigation" })), false);
```

- [ ] **Step 3: Run tests and verify all pass**

```bash
open /Users/jp/Projects/active/claude-code-tool-dev/page-turner/test-patterns.html
```

Expected: All tests PASS, 0 failed.

- [ ] **Step 4: Commit**

```bash
git add page-turner/test-patterns.html
git commit -m "feat(page-turner): add interactive element guard with tests"
```

---

### Task 5: Assemble background.js — navigatePage Function

**Files:**
- Create: `page-turner/background.js`

- [ ] **Step 1: Write the complete navigatePage function**

This function is serialized and injected into tabs. It must be fully self-contained — no references to anything outside the function body.

```javascript
function navigatePage(direction) {
  // Interactive element guard
  const el = document.activeElement;
  if (el) {
    const tag = el.tagName;
    if (
      tag === "TEXTAREA" || tag === "SELECT" || tag === "VIDEO" ||
      tag === "AUDIO" || tag === "IFRAME" || tag === "FRAME"
    ) {
      return { navigated: false };
    }
    if (tag === "INPUT") {
      const type = (el.type || "text").toLowerCase();
      const interactiveTypes = new Set([
        "text", "search", "number", "email", "url", "tel", "password",
        "range", "date", "time", "datetime-local", "month", "week", "color",
      ]);
      if (interactiveTypes.has(type)) return { navigated: false };
    }
    if (el.isContentEditable) return { navigated: false };
    const role = (el.getAttribute("role") || "").toLowerCase();
    const interactiveRoles = new Set([
      "textbox", "slider", "listbox", "menu", "menubar",
      "tree", "treegrid", "grid", "combobox", "spinbutton", "tablist",
    ]);
    if (interactiveRoles.has(role)) return { navigated: false };
  }

  // Numeric validation helper
  function parsePageNumber(value) {
    const result = parseInt(value, 10);
    if (isNaN(result) || result.toString() !== value || result < 0) return null;
    return result;
  }

  // Pattern registry
  const patterns = [
    {
      name: "query-page",
      match(url) {
        const params = new URLSearchParams(url.search);
        for (const key of ["page", "p", "pg"]) {
          const raw = params.get(key);
          if (raw === null) continue;
          const value = parsePageNumber(raw);
          if (value === null) continue;
          return {
            value,
            min: 1,
            build(n) {
              const newUrl = new URL(url.href);
              const newParams = new URLSearchParams(newUrl.search);
              newParams.set(key, n.toString());
              newUrl.search = newParams.toString();
              return newUrl.href;
            },
          };
        }
        return null;
      },
    },
    {
      name: "path-page-slash",
      match(url) {
        const regex = /\/page\/(\d+)(?=\/|$)/;
        const m = url.pathname.match(regex);
        if (!m) return null;
        const value = parsePageNumber(m[1]);
        if (value === null) return null;
        return {
          value,
          min: 1,
          build(n) {
            const newPathname = url.pathname.replace(regex, `/page/${n}`);
            const newUrl = new URL(url.href);
            newUrl.pathname = newPathname;
            return newUrl.href;
          },
        };
      },
    },
    {
      name: "path-page-hyphen",
      match(url) {
        const regex = /\/page-(\d+)(?=\/|$)/;
        const m = url.pathname.match(regex);
        if (!m) return null;
        const value = parsePageNumber(m[1]);
        if (value === null) return null;
        return {
          value,
          min: 1,
          build(n) {
            const newPathname = url.pathname.replace(regex, `/page-${n}`);
            const newUrl = new URL(url.href);
            newUrl.pathname = newPathname;
            return newUrl.href;
          },
        };
      },
    },
  ];

  // Navigation flow
  const url = new URL(window.location.href);
  for (const pattern of patterns) {
    const result = pattern.match(url);
    if (!result) continue;
    const newValue = result.value + direction;
    if (newValue < result.min) return { navigated: false };
    window.location.href = result.build(newValue);
    return { navigated: true };
  }

  return { navigated: false };
}
```

- [ ] **Step 2: Verify the function is self-contained**

Scan the function body for any references to variables outside its scope. The only external reference should be the `direction` parameter and browser globals (`document`, `window`, `URL`, `URLSearchParams`, `parseInt`, `isNaN`, `Set`).

Run: `grep -n 'api\.\|chrome\.\|browser\.\|PATTERNS\|parsePageNumber' page-turner/background.js`

Expected: No matches outside the function body. `parsePageNumber` should only appear as a nested function definition and calls within `navigatePage`.

- [ ] **Step 3: Commit**

```bash
git add page-turner/background.js
git commit -m "feat(page-turner): write navigatePage injection function"
```

---

### Task 6: Assemble background.js — Command Listener and In-Flight Guard

**Files:**
- Modify: `page-turner/background.js`

- [ ] **Step 1: Add the API shim, in-flight guard, and command listener**

Prepend to `page-turner/background.js` (before the `navigatePage` function):

```javascript
const api = globalThis.browser ?? globalThis.chrome;

const navigatingTabs = new Set();

api.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === "loading") {
    navigatingTabs.delete(tabId);
  }
});

api.tabs.onRemoved.addListener((tabId) => {
  navigatingTabs.delete(tabId);
});

api.commands.onCommand.addListener(async (command) => {
  if (command !== "next-page" && command !== "prev-page") return;
  const direction = command === "next-page" ? 1 : -1;

  const tabs = await api.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];
  if (!tab?.id || navigatingTabs.has(tab.id)) return;

  navigatingTabs.add(tab.id);

  try {
    const results = await api.scripting.executeScript({
      target: { tabId: tab.id },
      func: navigatePage,
      args: [direction],
    });

    const navigated = results?.[0]?.result?.navigated === true;
    if (!navigated) {
      navigatingTabs.delete(tab.id);
    } else {
      setTimeout(() => navigatingTabs.delete(tab.id), 5000);
    }
  } catch {
    navigatingTabs.delete(tab.id);
  }
});
```

- [ ] **Step 2: Review the complete background.js file**

Read the full file and verify:
- `api` shim is the first line
- `navigatingTabs` set and cleanup listeners come next
- Command listener follows
- `navigatePage` function is at the bottom
- No syntax errors, no dangling references

- [ ] **Step 3: Commit**

```bash
git add page-turner/background.js
git commit -m "feat(page-turner): add command listener and in-flight guard state machine"
```

---

### Task 7: Chrome Smoke Test

**Files:** None modified — manual testing only.

- [ ] **Step 1: Load extension in Chrome**

1. Open `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `page-turner/` directory
5. Verify the extension loads without errors (no red error badge)

- [ ] **Step 2: Verify shortcut registration**

1. Go to `chrome://extensions/shortcuts`
2. Find "Page Turner"
3. Verify `next-page` shows `Ctrl+Shift+Right` and `prev-page` shows `Ctrl+Shift+Left`
4. If the shortcuts are blank or conflicted, note the conflict and remap manually

- [ ] **Step 3: Test query-page pattern**

1. Navigate to `https://news.ycombinator.com/news?p=1`
2. Click somewhere on the page body (not a text input)
3. Press `Ctrl+Shift+Right`
4. Expected: URL changes to `?p=2`
5. Press `Ctrl+Shift+Left`
6. Expected: URL changes back to `?p=1`
7. Press `Ctrl+Shift+Left` again
8. Expected: Nothing happens (lower boundary, already at page 1)

- [ ] **Step 4: Test path-page-slash pattern**

Find a site using `/page/N` URLs, or manually type a URL like `https://example.com/page/3` and test navigation.

- [ ] **Step 5: Test interactive element guard**

1. On any matched page, click into a search/text input
2. Press `Ctrl+Shift+Right`
3. Expected: Nothing happens (guard blocks navigation)
4. Click away from the input (onto page body)
5. Press `Ctrl+Shift+Right`
6. Expected: Navigation works

- [ ] **Step 6: Test restricted page**

1. Navigate to `chrome://extensions/`
2. Press `Ctrl+Shift+Right`
3. Expected: Nothing happens (no errors in extension service worker console)

- [ ] **Step 7: Check service worker console for errors**

1. Go to `chrome://extensions/`
2. Click "service worker" link under Page Turner
3. Check console for any errors
4. Expected: No errors (restricted page attempts are silently caught)

- [ ] **Step 8: Commit (test harness cleanup — optional)**

If all smoke tests pass, optionally remove the test harness files since they served their purpose:

```bash
git add page-turner/patterns.js page-turner/test-patterns.html
git commit -m "test(page-turner): keep pattern test harness for future regression testing"
```

---

### Task 8: Firefox Smoke Test

**Files:** None modified — manual testing only.

- [ ] **Step 1: Load extension in Firefox**

1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on…"
3. Select `page-turner/manifest.json`
4. Verify the extension loads without errors

- [ ] **Step 2: Verify shortcut registration**

1. Open `about:addons` → click gear icon → "Manage Extension Shortcuts"
2. Find "Page Turner"
3. Verify shortcuts are registered. If `MacCtrl+Shift` doesn't register as expected, note the behavior.

- [ ] **Step 3: Test the critical API path**

1. Navigate to a page with `?page=1`
2. Press `Ctrl+Shift+Right`
3. Expected: URL changes to `?page=2`
4. If it does NOT work, open the extension console (`about:debugging` → Inspect) and check for errors.

**Key check:** verify that `await api.scripting.executeScript(...)` returns the expected `InjectionResult[]` shape. If Firefox returns a different shape or the promise doesn't resolve, the `browser.*` primary path in the namespace shim should handle it. If not, add a per-call wrapper as noted in the spec.

- [ ] **Step 4: Test interactive element guard in Firefox**

1. Click into a text input on the test page
2. Press `Ctrl+Shift+Right`
3. Expected: Nothing happens

- [ ] **Step 5: Document any Firefox-specific issues**

If anything behaves differently from Chrome, document it and fix before committing:
- Shortcut format differences
- API namespace issues
- Result shape differences
- Permission prompt differences

---

### Task 9: Final Cleanup and Documentation

**Files:**
- Modify: `page-turner/manifest.json` (only if Firefox smoke test revealed issues)
- Modify: `page-turner/background.js` (only if Firefox smoke test revealed issues)

- [ ] **Step 1: Apply any fixes from Firefox smoke test**

If Task 8 revealed issues, fix them. Common issues:
- Firefox may need `browser_specific_settings` in manifest for `about:addons` to recognize commands
- The `InjectionResult` shape may differ — adjust the result reading logic

- [ ] **Step 2: Final review of background.js**

Read the complete file one more time. Check:
- No console.log statements left in (unless intentional for dev)
- All state machine transitions have matching cleanup paths
- `navigatePage` is self-contained
- No TODO comments

- [ ] **Step 3: Final commit**

```bash
git add page-turner/
git commit -m "feat(page-turner): complete browser extension for paginated navigation

Two-file MV3 extension (Chrome + Firefox on macOS).
Ctrl+Shift+Arrow shortcut navigates ?page=N, /page/N, /page-N URLs.
Commands API + activeTab + scripting for on-demand injection.
Background in-flight guard prevents double-navigation."
```

---

## Self-Review

**Spec coverage check:**

| Spec Section | Task |
|-------------|------|
| Manifest (commands, background, permissions) | Task 1 |
| Cross-browser background (`scripts` + `service_worker`) | Task 1 |
| Cross-browser API namespace (`browser ?? chrome`) | Task 6 |
| Shortcut (`MacCtrl+Shift+Left/Right`) | Task 1, verified Task 7 Step 2 |
| `activeTab` + `scripting` permissions | Task 1 |
| Pattern: `query-page` | Task 2 |
| Pattern: `path-page-slash` | Task 3 |
| Pattern: `path-page-hyphen` | Task 3 |
| Numeric validation (`parseInt`, `toString`, `< 0`) | Task 2 (in `parsePageNumber`) |
| Duplicate query params (first occurrence) | Task 2 test |
| Regex boundaries (segment boundaries, lookahead) | Task 3 |
| Interactive element guard (all element types + ARIA roles) | Task 4, Task 5 |
| In-flight guard state machine (all transitions) | Task 6 |
| Injection result reading (`results[0].result.navigated`) | Task 6 |
| Error handling (try/catch, cleanup) | Task 6 |
| 5-second timeout failsafe | Task 6 |
| `tabs.onUpdated`/`onRemoved` cleanup | Task 6 |
| Navigation flow (guard → parse → match → bound-check → navigate) | Task 5 |
| Return `{ navigated: boolean }` from all exits | Task 5 |
| Function serialization (self-contained) | Task 5 Step 2 |
| Chrome smoke test | Task 7 |
| Firefox smoke test + API verification | Task 8 |
| Restricted page behavior | Task 7 Step 6 |
| Below-min recovery (`?page=0` + next → `?page=1`) | Task 2 test |
| Iframe guard | Task 4 |
| Lower boundary (do nothing) | Task 7 Step 3 |

**Placeholder scan:** No TBDs, TODOs, "fill in later", or vague steps found.

**Type consistency:** `parsePageNumber` name consistent across Task 2, 3, 5. `navigatePage` consistent across Task 5, 6. `navigatingTabs` consistent within Task 6. `{ navigated: boolean }` return type consistent across Task 5 and 6. Pattern interface (`name`, `match`, `value`, `min`, `build`) consistent across all pattern tasks.
