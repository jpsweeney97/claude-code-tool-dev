# Page Turner — Browser Extension Design

## Purpose

A browser extension for Mac that navigates paginated websites via keyboard shortcut. Detects page-number patterns in URLs and increments/decrements them when the user presses a modifier+arrow chord.

Personal utility — not targeting store distribution.

## Targets

- Chrome on macOS
- Firefox on macOS
- Manifest V3

Firefox MV3 aims for Chrome compatibility but diverges in some areas. For this extension's surface (content scripts, commands, messaging), the APIs are aligned.

## File Structure

```
page-turner/
├── manifest.json    # Extension manifest (V3), commands, content script
├── background.js    # Command listener → message relay to active tab
└── content.js       # Pattern registry + navigation handler
```

## Manifest

```json
{
  "manifest_version": 3,
  "name": "Page Turner",
  "version": "1.0",
  "description": "Navigate paginated sites with a keyboard shortcut",
  "commands": {
    "next-page": {
      "suggested_key": { "mac": "MacCtrl+Right" },
      "description": "Go to next page"
    },
    "prev-page": {
      "suggested_key": { "mac": "MacCtrl+Left" },
      "description": "Go to previous page"
    }
  },
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "all_frames": false
  }]
}
```

### Shortcut Rationale

`MacCtrl+Left/Right` uses the physical Ctrl key on Mac. macOS uses Cmd as its primary modifier, so the Ctrl key is largely unused in browsers and system shortcuts. Verified clear of conflicts with:
- `Cmd+Left/Right` (line start/end, browser back/forward)
- `Option+Left/Right` (word jump)
- `Cmd+[/]` (browser back/forward)

Users can remap in `chrome://extensions/shortcuts` (Chrome) or `about:addons` (Firefox).

### Permissions and Host Access

The `content_scripts.matches: ["<all_urls>"]` field grants broad host access — the content script injects into every page. This means:

- Chrome and Firefox will show an "access your data on all websites" prompt at install.
- Firefox allows users to revoke host permissions per-site.
- Content scripts do not run on restricted pages (`chrome://`, `about:`, `addons.mozilla.org`, extension pages).
- No explicit `"permissions"` array is needed — the extension uses no extension APIs beyond `commands` and `runtime.onMessage`.

For personal sideloaded use, this is acceptable. For store distribution, a narrower host list or `activeTab` permission would be more appropriate.

## Architecture

### Commands API (Primary Shortcut Handling)

The browser's Commands API provides the keyboard shortcut layer:

1. User presses `Ctrl+Right` (physical Ctrl on Mac).
2. Browser fires a `commands.onCommand` event in the background service worker.
3. Background sends a `{ direction: "next" | "prev" }` message to the active tab.
4. Content script receives the message, runs pattern matching, navigates.

This architecture means shortcuts are user-configurable via browser settings and benefit from the browser's built-in conflict detection.

### Background Service Worker

Minimal relay (~10 lines). Listens for command events, sends a message to the active tab's content script. No state, no storage, no other logic.

### Content Script: Pattern Registry

The content script has two parts: a pattern registry and a message handler.

#### Pattern Interface

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

#### Pattern List (checked in order, first match wins)

| # | Name | Detects | Min | Examples |
|---|------|---------|-----|----------|
| 1 | `query-page` | `?page=N`, `?p=N`, `?pg=N` | 1 | `?page=4`, `?p=2` |
| 2 | `path-page-slash` | `/page/N` in path | 1 | `/results/page/3` |
| 3 | `path-page-hyphen` | `/page-N` in path | 1 | `/results/page-3` |

**Removed patterns:**
- `?offset=N` — offset pagination increments by page size (10, 20, 50), not by 1. Without knowing the page size, incrementing by 1 is almost always wrong. Dropped rather than shipped broken.
- `/<word>/N` catch-all — matches IDs, years, product numbers, and other non-pagination numerics. False-positive rate too high for a global default.

**Query param patterns:** Use `URLSearchParams` to read and write the param value. Preserve all other params, path, and hash.

**Path patterns:** Use regex against `url.pathname`. Replace only the matched number segment, preserving query string and hash.

### Content Script: Message Handler

#### Flow

1. Receive message from background: `{ direction: "next" | "prev" }`.
2. **Interactive element guard:** is the focused element interactive? If so, ignore. (Backup safety — the Commands API is the primary conflict-avoidance layer, but this catches edge cases where the chord might interfere with a focused widget.)
3. Parse current URL: `new URL(window.location.href)`.
4. Loop through `PATTERNS` — first match wins.
5. Compute `newValue = value + (direction === "next" ? 1 : -1)`.
6. If `newValue < min`, return (do nothing at lower boundary).
7. Clear in-flight guard, navigate: `window.location.href = build(newValue)`.

#### Interactive Element Guard

Skip navigation when `document.activeElement` is any of:

- `<input>` with a text-like type (`text`, `search`, `number`, `email`, `url`, `tel`, `password`)
- `<input>` with interactive types (`range`, `date`, `time`, `datetime-local`, `month`, `week`, `color`)
- `<textarea>`
- `<select>`
- `<video>` or `<audio>`
- Any element where `element.isContentEditable === true` (handles nested contenteditable and shadow DOM better than checking the attribute string)
- Any element with an ARIA role that implies arrow-key interaction: `textbox`, `slider`, `listbox`, `menu`, `menubar`, `tree`, `treegrid`, `grid`, `combobox`, `spinbutton`, `tablist`

This guard is a backup. The primary protection is the modifier chord itself — these controls rarely bind to `Ctrl+Arrow` on Mac.

#### In-Flight Guard

A module-scoped boolean (`navigating = false`) prevents double-navigation from rapid keypresses. Set to `true` before `window.location.href` assignment. Not reset — the page load destroys the content script.

## Behaviors

- **Lower boundary:** Shortcut at page 1 does nothing.
- **Upper boundary:** No upper limit enforced — the target site handles invalid page numbers.
- **No visual feedback:** No toasts, badges, or popups.
- **Top frame only:** `all_frames: false` in the manifest. The content script runs only in the top-level frame, avoiding confusion when pagination URLs appear in iframes.
- **Restricted pages:** Content scripts do not run on `chrome://`, `about:`, browser extension pages, or Firefox restricted domains. The shortcut simply does nothing on these pages.

## Non-Goals

- Store distribution or cross-platform support
- Per-site configuration or settings UI
- Detecting pagination links in page HTML (URL patterns only)
- Offset-based pagination
- Catch-all path-segment matching
- Infinite scroll support
- Wrap-around navigation
