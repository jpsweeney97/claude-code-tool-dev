# Page Turner — Browser Extension Design

## Purpose

A browser extension for Mac that navigates paginated websites via keyboard shortcut. Detects page-number patterns in URLs and increments/decrements them when the user presses a modifier+arrow chord.

Personal utility — not targeting store distribution.

## Targets

- Chrome on macOS
- Firefox on macOS
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

Users can remap in `chrome://extensions/shortcuts` (Chrome) or `about:addons` (Firefox).

### Permissions

**`activeTab`** — grants temporary host access to the active tab when the user invokes a registered command (including keyboard shortcuts). Access is scoped to that single invocation; no persistent broad access.

**`scripting`** — required to call `chrome.scripting.executeScript`, which injects the navigation function into the active tab on demand.

No `<all_urls>` or host permissions. The extension only touches a tab when the user explicitly presses the shortcut. Chrome shows this as "can read and change site data when you click the extension" — much narrower than "on all websites."

Content scripts do not run on restricted pages (`chrome://`, `about:`, `addons.mozilla.org`, extension pages). On these pages, `scripting.executeScript` throws; the background catches and ignores the error.

## Architecture

### On-Demand Injection via Commands API

1. User presses `Ctrl+Shift+Right` (physical Ctrl on Mac).
2. Browser fires a `commands.onCommand` event in the background.
3. Background queries the active tab and calls `scripting.executeScript` with a self-contained navigation function and the direction as an argument.
4. The injected function runs in the page context: checks interactive element guard, matches URL patterns, navigates.

No persistent content script. No message passing. The navigation logic is injected fresh on each invocation.

### Background Script

~30 lines. Two responsibilities:

1. **Command listener:** maps `"next-page"` / `"prev-page"` to a direction value (`1` or `-1`).
2. **Injection:** calls `scripting.executeScript({ target: { tabId }, func: navigatePage, args: [direction] })`.

Error handling: wraps `executeScript` in try/catch. Expected errors (restricted page, no tab, host permission unavailable) are silently ignored — the shortcut simply does nothing.

The `navigatePage` function is defined in `background.js` but runs in the tab's page context. Because `scripting.executeScript` serializes the function, it must be fully self-contained — no closures over external variables, no imports.

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
- Any element where `element.isContentEditable === true`
- Any element with an ARIA role that implies arrow-key interaction: `textbox`, `slider`, `listbox`, `menu`, `menubar`, `tree`, `treegrid`, `grid`, `combobox`, `spinbutton`, `tablist`

This guard is a backup safety layer. The primary conflict-avoidance mechanism is the modifier chord itself.

#### In-Flight Guard

Before navigating, check a marker on `document` (`document.__pageTurnerNavigating`). If set, return. Otherwise set it, then navigate.

Each `scripting.executeScript` call runs a fresh function invocation in the existing page context. If the user presses the shortcut twice rapidly, the second invocation sees the marker from the first and bails. The page load destroys the marker.

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

#### Navigation Flow

1. **In-flight guard:** if `document.__pageTurnerNavigating` is truthy, return.
2. **Interactive element guard:** if focused element is interactive (see guard definition above), return.
3. Parse current URL: `new URL(window.location.href)`.
4. Loop through `PATTERNS` — first match wins.
5. No match: return (URL has no recognized pagination pattern).
6. Compute `newValue = value + direction`.
7. If `newValue < min`, return (do nothing at lower boundary).
8. Set `document.__pageTurnerNavigating = true`.
9. Navigate: `window.location.href = build(newValue)`.

## Behaviors

- **Lower boundary:** shortcut at page 1 does nothing.
- **Upper boundary:** no upper limit enforced — the target site handles invalid page numbers.
- **No visual feedback:** no toasts, badges, or popups.
- **Restricted pages:** `scripting.executeScript` throws on `chrome://`, `about:`, browser extension pages, and Firefox restricted domains. Background catches and ignores the error.
- **Iframes:** not applicable. On-demand injection targets the top-level tab, not frames. The focused element check operates on the top document's `activeElement`.

## Non-Goals

- Store distribution or cross-platform support
- Per-site configuration or settings UI
- Detecting pagination links in page HTML (URL patterns only)
- Offset-based pagination
- Catch-all path-segment matching
- Infinite scroll support
- Wrap-around navigation
