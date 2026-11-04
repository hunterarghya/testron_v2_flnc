// One self-contained HTML file (ADR-019, frontend_spec.md §6): the page's own styles inlined,
// the fonts as data URIs, nothing fetched but the images (by their ImageKit address).
// Opening it needs only a browser, and "Save as PDF" works.

const PAGE_RULES = 'main{max-width:56rem;margin:2rem auto;padding:0 1rem}@media print{body{background:#fff}}'

/** Every style rule the page uses now, without its @font-face rules (their files are on the
 *  server; the document brings its own). */
export function collectCss(sheets: Iterable<CSSStyleSheet> = document.styleSheets): string {
  const rules: string[] = []
  for (const sheet of sheets) {
    try {
      for (const rule of Array.from(sheet.cssRules)) {
        if (!rule.cssText.startsWith('@font-face')) rules.push(rule.cssText)
      }
    }
    catch {
      // A stylesheet from another origin can't be read; the app has none, so skip it
    }
  }
  return rules.join('\n')
}

export function escapeHtml(text: string): string {
  return text.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!)
}

export function htmlDocument(title: string, body: string, css: string): string {
  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<title>${escapeHtml(title)}</title>`,
    `<style>${css}\n${PAGE_RULES}</style>`,
    '</head>',
    `<body><main>${body}</main></body>`,
    '</html>',
  ].join('\n')
}
