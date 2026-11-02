// Marks and numerical answers arrive as decimal strings ("4.00"); people read "4".
// They are never turned into floats (CLAUDE.md rule 7).

/** "4.00" → "4", "2.50" → "2.5", "120" → "120". */
export function formatDecimal(value: string): string {
  return value.includes('.') ? value.replace(/\.?0+$/, '') : value
}
