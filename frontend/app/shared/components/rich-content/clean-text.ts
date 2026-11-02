// The same text cleaning as the server's (editor_content_spec.md §3, core/rich_content/normalize.py),
// applied when text is pasted: NFC; control characters, the byte-order mark and bidi overrides
// removed; tabs become spaces. The zero-width joiner and non-joiner stay (Bengali conjuncts).

const BYTE_ORDER_MARK = 0xFEFF
const isBidiControl = (code: number) => (code >= 0x202A && code <= 0x202E) || (code >= 0x2066 && code <= 0x2069)
// C0 and C1 control characters, except newline (kept) and tab (made a space first)
const isControl = (code: number) => (code < 0x20 && code !== 0x0A) || (code >= 0x7F && code <= 0x9F)

export function cleanText(raw: string): string {
  let kept = ''
  for (const character of raw.normalize('NFC').replaceAll('\t', ' ')) {
    const code = character.codePointAt(0)!
    if (code === BYTE_ORDER_MARK || isBidiControl(code) || isControl(code)) continue
    kept += character
  }
  return kept
}
