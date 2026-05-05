# Page Turner — Browser Extension Design

## Purpose

A minimal browser extension that lets users navigate paginated websites using the left and right arrow keys. Detects page numbers in URLs and increments/decrements them on keypress.

## Targets

- Chrome (and Chromium-based browsers)
- Firefox
- Manifest V3 (supported by both)

## File Structure

```
page-turner/
├── manifest.json    # Extension manifest (V3)
└── content.js       # Pattern registry + keyboard handler
```

No background worker, no popup, no settings UI.

## Manifest

```json
{
  "manifest_version": 3,
  "name": "Page Turner",
  "version": "1.0",
  "description": "Navigate paginated sites with arrow keys",
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }]
}
```

No special permissions required. Content scripts can read and set `window.location` natively.

## Architecture: Pattern Registry

The content script has two parts: a pattern registry and a keyboard handler.

### Pattern Interface

Each pattern is an object:

```javascript
{
  name: string,
  match(url: URL): null | { value: number, min: number, build(n: number): string }
}
```

- `name` — human-readable identifier
- `match(url)` — returns `null` if the pattern doesn't apply to this URL, or an object with:
  - `value` — the current page/offset number
  - `min` — the floor value (1 for page patterns, 0 for offset)
  - `build(n)` — returns the full URL string with `n` substituted in. Uses closures to capture the original URL context.

### Pattern List (checked in order, first match wins)

| # | Name | Detects | Min | Examples |
|---|------|---------|-----|----------|
| 1 | `query-page` | `?page=N`, `?p=N`, `?pg=N` | 1 | `?page=4`, `?p=2` |
| 2 | `query-offset` | `?offset=N` | 0 | `?offset=20` |
| 3 | `path-page-slash` | `/page/N` in path | 1 | `/results/page/3` |
| 4 | `path-page-hyphen` | `/page-N` in path | 1 | `/results/page-3` |
| 5 | `path-category-number` | `/<word>/N` at end of path | 1 | `/videos/5`, `/top-rated/3/` |

**Order matters.** Specific patterns (query params, explicit `/page/`) come before the broader `/<word>/N` catch-all. A URL like `/page/3` matches pattern 3, not pattern 5.

### Pattern Details

**Query param patterns (1-2):** Use `URLSearchParams` to read and write the param. Preserve all other params, path, and hash.

**Path patterns (3-5):** Use regex against `url.pathname`. Reconstruct the URL with the number replaced, preserving query string and hash.

**Category-number pattern (5):** Matches a trailing `/<word>/<number>` or `/<word>/<number>/` in the path, where `<word>` is one or more word characters (letters, digits, underscores) or hyphens. This covers `/videos/5`, `/top-rated/3/`, `/best-sellers/2`, `/trending_topics/4/`.

## Keyboard Handler

Single `keydown` listener on `document`.

### Flow

1. Is the key `ArrowLeft` or `ArrowRight`? If not, return.
2. Is `document.activeElement` a text input? If so, return.
3. Loop through `PATTERNS` with `new URL(window.location.href)`.
4. First match: compute `newValue = value + (right ? 1 : -1)`.
5. If `newValue < min`, return (do nothing at lower boundary).
6. Navigate: `window.location.href = build(newValue)`.

### Text Input Detection

Skip navigation when the active element is any of:
- `<input>` with a text-like type: `text`, `search`, `number`, `email`, `url`, `tel`, `password`
- `<textarea>`
- Any element with `contentEditable` set to `"true"` or `""` (empty string also means editable)

All other focused elements (body, links, buttons, divs) allow navigation.

## Behaviors

- **Lower boundary:** Left arrow on page 1 (or offset 0) does nothing.
- **Upper boundary:** No upper limit enforced — the site handles invalid high page numbers.
- **Offset increment:** Always 1 (the site rounds/clamps to valid offsets).
- **No debounce:** Navigation triggers a full page load, so the listener is gone before a repeat keypress.
- **No state:** Each keypress parses the URL fresh. Nothing stored between events.
- **No visual feedback:** No toasts, badges, or popups.

## Non-Goals

- Per-site configuration or settings UI
- Detecting pagination links in page HTML (we only read the URL)
- Infinite scroll support
- Modifier key combos
- Wrap-around navigation
