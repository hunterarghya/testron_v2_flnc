// The app's fonts as data URIs (ADR-019): an exported file shows Bengali correctly on any
// computer, with nothing to fetch. Imported only when an export runs, so the screens never
// load them.
import bengali400 from '@fontsource/noto-sans-bengali/files/noto-sans-bengali-bengali-400-normal.woff2?inline'
import bengali600 from '@fontsource/noto-sans-bengali/files/noto-sans-bengali-bengali-600-normal.woff2?inline'
import inter400 from '@fontsource/inter/files/inter-latin-400-normal.woff2?inline'
import inter600 from '@fontsource/inter/files/inter-latin-600-normal.woff2?inline'

const FONTS = [
  { family: 'Inter', weight: 400, url: inter400 },
  { family: 'Inter', weight: 600, url: inter600 },
  { family: 'Noto Sans Bengali', weight: 400, url: bengali400 },
  { family: 'Noto Sans Bengali', weight: 600, url: bengali600 },
]

export function fontFaces(): string {
  return FONTS.map(f => `@font-face{font-family:'${f.family}';font-weight:${f.weight};font-style:normal;src:url(${f.url}) format('woff2')}`).join('\n')
}
