# Page Turner — Browser Extension Design

## Purpose

A browser extension for Mac that navigates paginated websites via keyboard shortcut. Detects page-number patterns in URLs and increments/decrements them when the user presses a modifier+arrow chord.

Personal utility — not targeting store distribution.

## Targets

- Current Chrome on macOS (no minimum version pinned — personal use, always up to date)
- Current Firefox on macOS
- Manifest V3

Firefox MV3 aims for Chrome compatibility but diverges in the background script model. This design accounts for the divergence (see Manifest section).

## File Structure

```
page-turner/
├── manifest.json    # Extension manifest (V3), commands, permissions
└── background.js    # Command listener + injected navigation logic
```

Two files. No persistent content script.

## Manifest

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

### Cross-Browser Background

Chrome MV3 reads `background.service_worker` and ignores `scripts`. Firefox MV3 reads `background.scripts` and ignores `service_worker`. Including both in the same manifest is the documented cross-browser pattern. The background code must work under both execution models (service worker on Chrome, event page on Firefox). For this extension's minimal surface — a single `commands.onCommand` listener — both models behave identically.

### Shortcut Rationale

`MacCtrl+Shift+Left/Right` uses the physical Ctrl key + Shift on Mac.

**Why not `MacCtrl+Left/Right` (without Shift)?** macOS reserves `Ctrl+Left/Right` for Mission Control Spaces navigation by default. The OS captures it before the browser sees it.

`Ctrl+Shift+Left/Right` is free of known conflicts:
- Not used by macOS system shortcuts (Mission Control uses Ctrl+Arrow without Shift)
- Not used by Chrome or Firefox for built-in navigation
- Not a standard text-editing chord on macOS (Cmd and Option handle text selection)

This is the default candidate. After install, verify the shortcut registered by checking `chrome://extensions/shortcuts` (Chrome) or `about:addons` (Firefox). Browser/OS shortcuts can take priority over extension commands; if the chord is swallowed, remap in those same settings pages.

### Permissions

**`activeTab`** — grants temporary host access to the active tab when the user invokes a registered command (including keyboard shortcuts). This is a hard dependency: the Commands API command invocation is what triggers the `activeTab` grant, which in turn permits `scripting.executeScript` on that tab. Access is scoped to that single invocation; no persistent broad access.

**`scripting`** — required to call `chrome.scripting.executeScript`, which injects the navigation function into the active tab on demand.

No `<all_urls>` or host permissions. The extension only touches a tab when the user explicitly presses the shortcut. Chrome shows this as "can read and change site data when you click the extension" — much narrower than "on all websites."

Content scripts do not run on restricted pages (`chrome://`, `about:`, `addons.mozilla.org`, extension pages). On these pages, `scripting.executeScript` throws; the background catches and ignores the error.

## Architecture

### On-Demand Injection via Commands API

1. User presses `Ctrl+Shift+Right` (physical Ctrl on Mac).
2. Browser fires a `commands.onCommand` event in the background.
3. Background queries the active tab and calls `scripting.executeScript` with a self-contained navigation function and the direction as an argument.
4. The injected function runs in the tab's isolated content-script world: checks interactive element guard, matches URL patterns, navigates.

No persistent content script. No message passing. The navigation logic is injected fresh on each invocation.

### Background Script

~40 lines. Three responsibilities:

1. **Command listener:** maps `"next-page"` / `"prev-page"` to a direction value (`1` or `-1`).
2. **In-flight guard:** maintains a `Set` of tab IDs currently navigating. Before injecting, checks if the tab is already in the set. Adds the tab ID before injection. Cleans up via `tabs.onUpdated` (when `status` changes to `"loading"`, the navigation started — remove the tab from the set) and `tabs.onRemoved` (tab closed). This prevents double-navigation from rapid shortcut presses.
3. **Injection:** calls `scripting.executeScript({ target: { tabId }, func: navigatePage, args: [direction] })`.

Error handling: wraps `executeScript` in try/catch. On restricted pages, missing tabs, or unavailable host permissions, `executeScript` throws. In development, log these to the service worker console to distinguish real bugs from expected no-ops. In production, silently ignore — the shortcut simply does nothing.

The `navigatePage` function is defined in `background.js` but executes in the tab's isolated content-script world (the default `scripting.ExecutionWorld`). It is NOT the page's main JS world — the function cannot access page-defined globals, and custom expando properties on DOM objects may not persist predictably across injection calls. Because `scripting.executeScript` serializes the function, it must be fully self-contained — no closures over external variables, no imports.

### Injected Function: `navigatePage(direction)`

Self-contained function that receives `direction` (1 or -1) as its argument. Contains the pattern registry, interactive element guard, and navigation logic.

#### Interactive Element Guard

First check: is the focused element interactive? If so, return without navigating.

Skip navigation when `document.activeElement` is any of:

- `<input>` with a text-like type (`text`, `search`, `number`, `email`, `url`, `tel`, `password`)
- `<input>` with interactive types (`range`, `date`, `time`, `datetime-local`, `month`, `week`, `color`)
- `<textarea>`
- `<select>`
- `<video>` or `<audio>`
- `<iframe>` or `<frame>` (focus inside an iframe means the user is interacting with embedded content; the top document's `activeElement` is the iframe element itself)
- Any element where `element.isContentEditable === true`
- Any element with an ARIA role that implies arrow-key interaction: `textbox`, `slider`, `listbox`, `menu`, `menubar`, `tree`, `treegrid`, `grid`, `combobox`, `spinbutton`, `tablist`

This guard is a backup safety layer. The primary conflict-avoidance mechanism is the modifier chord itself.

#### Pattern Registry

##### Pattern Interface

Each pattern is an object:

```javascript
{
  name: string,
  match(url: URL): null | { value: number, min: number, build(n: number): string }
}
```

- `name` — human-readable identifier for debugging.
- `match(url)` — returns `null` if the pattern doesn't apply, or:
  - `value` — the current page number.
  - `min` — the floor value (1 for all current patterns).
  - `build(n)` — returns the full URL string with `n` substituted. Uses closures to capture the original URL context, preserving all other URL components (other params, hash, path segments).

##### Pattern List (checked in order, first match wins)

| # | Name | Detects | Min | Examples |
|---|------|---------|-----|----------|
| 1 | `query-page` | `?page=N`, `?p=N`, `?pg=N` | 1 | `?page=4`, `?p=2` |
| 2 | `path-page-slash` | `/page/N` in path | 1 | `/results/page/3` |
| 3 | `path-page-hyphen` | `/page-N` in path | 1 | `/results/page-3` |

**`?p=N` note:** `p` is ambiguous — it can mean page, post, product, or profile. Kept because: (a) modifier chord prevents accidental triggering, (b) the worst case is navigating to a wrong page, not losing data, (c) personal use means we know which sites we visit.

**Removed patterns:**
- `?offset=N` — offset pagination increments by page size (10, 20, 50), not by 1. Without knowing the page size, incrementing by 1 is almost always wrong.
- `/<word>/N` catch-all — matches IDs, years, product numbers, and other non-pagination numerics. False-positive rate too high for a default matcher.

##### Pattern Details

**Query param patterns:** Use `URLSearchParams` to read and write the param value. Preserve all other params, path, and hash.

**Path patterns:** Use regex against `url.pathname`. Replace only the matched number segment, preserving query string and hash.

##### Numeric Validation

Pattern matchers must validate that the extracted value is a base-10 positive integer:
- Parse with `parseInt(value, 10)`.
- Reject (return `null`) if `isNaN(result)` or `result.toString() !== value` (catches `01`, `1.5`, `1abc`).
- Reject if `result < 0`.

For query params with duplicate keys (e.g., `?page=1&page=2`), use the first occurrence.

#### Navigation Flow

1. **Interactive element guard:** if focused element is interactive (see guard definition above), return.
2. Parse current URL: `new URL(window.location.href)`.
3. Loop through `PATTERNS` — first match wins.
4. No match: return (URL has no recognized pagination pattern).
5. Compute `newValue = value + direction`.
6. If `newValue < min`, return (do nothing at lower boundary).
7. Navigate: `window.location.href = build(newValue)`.

The in-flight guard lives in the background script (see Background Script section), not in the injected function. This avoids depending on cross-injection state persistence in the isolated content-script world.

## Behaviors

- **Lower boundary:** shortcut at page 1 does nothing.
- **Upper boundary:** no upper limit enforced — the target site handles invalid page numbers.
- **No visual feedback:** no toasts, badges, or popups.
- **Restricted pages:** `scripting.executeScript` throws on `chrome://`, `about:`, browser extension pages, and Firefox restricted domains. Background catches and ignores the error.
- **Iframes:** on-demand injection targets the top-level tab. If focus is inside an iframe, the top document's `activeElement` is the `<iframe>` element itself, which the interactive element guard treats as interactive — navigation is skipped.

## Non-Goals

- Store distribution or cross-platform support
- Per-site configuration or settings UI
- Detecting pagination links in page HTML (URL patterns only)
- Offset-based pagination
- Catch-all path-segment matching
- Infinite scroll support
- Wrap-around navigation
