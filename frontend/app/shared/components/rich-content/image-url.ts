// How an image is shown (editor_content_spec.md §2.3, §5.2): its `size` is a share of the content
// column, never wider than the original; the file is fetched resized by the CDN, in a few fixed
// widths so its cache stays effective.
export type ImageSize = 'S' | 'M' | 'L' | 'FULL'

export const SIZE_CLASS: Record<ImageSize, string> = { S: 'w-1/4', M: 'w-1/2', L: 'w-3/4', FULL: 'w-full' }
const SIZE_SHARE: Record<ImageSize, number> = { S: 0.25, M: 0.5, L: 0.75, FULL: 1 }
// The widest the content column gets (frontend_spec.md §2)
const COLUMN_PX = 760
const STEPS = [400, 800, 1200, 1600, 2400]

/** The address with an ImageKit resize, e.g. `…/golgi.png?tr=w-800,q-80,f-auto`. */
export function displayUrl(src: string, size: ImageSize, pixelRatio = globalThis.devicePixelRatio || 1): string {
  const wanted = COLUMN_PX * SIZE_SHARE[size] * pixelRatio
  const width = STEPS.find(step => step >= wanted) ?? STEPS[STEPS.length - 1]!
  return `${src}?tr=w-${width},q-80,f-auto`
}
