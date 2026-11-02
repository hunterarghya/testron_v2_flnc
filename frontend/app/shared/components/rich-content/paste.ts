// The paste pipeline (editor_content_spec.md §4.3): pasted HTML from Word, Google Docs, web
// pages or PDF viewers is tidied before the editor reads it. The editor's schema then keeps only
// the allowed formatting (bold, italic, underline, sub/superscript, lists, tables), so this step
// removes what the schema would misread and handles images:
// - embedded images (data: URLs) are taken out, to be uploaded;
// - remote images are taken out and counted ("1 image couldn't be copied, so upload it").
import { cleanText } from '~/shared/components/rich-content/clean-text'

export interface CleanPaste {
  html: string
  dataImages: string[]
  remoteImages: number
}

// Never content: Word's and web pages' furniture, and Word's list bullets (noted first, below)
const DROPPED_TAGS = new Set(['style', 'script', 'meta', 'link', 'title', 'xml', 'o:p'])

const styleOf = (element: Element) => (element.getAttribute('style') ?? '').toLowerCase()
const isWordBullet = (element: Element) => styleOf(element).includes('mso-list:ignore')
const isWordListItem = (element: Element) => element.tagName === 'P' && styleOf(element).includes('mso-list')

/** Plain filtering rather than CSS selectors: Word's `o:p` tags and case-insensitive style
 * matching then work the same in every browser (and in tests). */
function elements(root: HTMLElement, keep: (element: Element) => boolean): HTMLElement[] {
  return [...root.querySelectorAll<HTMLElement>('*')].filter(keep)
}

export function cleanPastedHtml(html: string): CleanPaste {
  const page = new DOMParser().parseFromString(html, 'text/html')
  const body = page.body
  removeComments(body)
  markWordListMarkers(body)
  elements(body, el => DROPPED_TAGS.has(el.tagName.toLowerCase()) || isWordBullet(el)).forEach(node => node.remove())
  const images = takeImages(body)
  wordListsToLists(body)
  cleanTextNodes(body)
  return { html: body.innerHTML, ...images }
}

function removeComments(root: HTMLElement): void {
  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_COMMENT)
  const comments: Node[] = []
  while (walker.nextNode()) comments.push(walker.currentNode)
  comments.forEach(comment => comment.parentNode?.removeChild(comment))
}

function takeImages(root: HTMLElement): { dataImages: string[], remoteImages: number } {
  const dataImages: string[] = []
  let remoteImages = 0
  root.querySelectorAll('img').forEach((image) => {
    const src = image.getAttribute('src') ?? ''
    if (src.startsWith('data:image/')) dataImages.push(src)
    else remoteImages++
    image.remove()
  })
  return { dataImages, remoteImages }
}

function cleanTextNodes(root: HTMLElement): void {
  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  while (walker.nextNode()) {
    const node = walker.currentNode
    node.textContent = cleanText(node.textContent ?? '')
  }
}

/** Word writes lists as paragraphs styled `mso-list` (its bullet glyphs were removed above);
 * runs of them become real lists. A run whose first marker was a number or letter is ordered. */
function wordListsToLists(root: HTMLElement): void {
  const items = elements(root, isWordListItem)
  let list: HTMLElement | null = null
  for (const paragraph of items) {
    const continues = list !== null && list.nextElementSibling === paragraph
    if (!continues) {
      list = root.ownerDocument.createElement(isOrdered(paragraph) ? 'ol' : 'ul')
      paragraph.before(list)
    }
    const item = root.ownerDocument.createElement('li')
    const text = root.ownerDocument.createElement('p')
    text.append(...paragraph.childNodes)
    item.append(text)
    list!.append(item)
    paragraph.remove()
  }
}

/** Word's list marker ("1.", "a)", "·") sits in a span that is dropped; it is noted first. */
function markWordListMarkers(root: HTMLElement): void {
  for (const paragraph of elements(root, isWordListItem)) {
    const marker = [...paragraph.querySelectorAll('*')].find(isWordBullet)
    paragraph.dataset.marker = marker?.textContent?.trim() ?? ''
  }
}

function isOrdered(paragraph: HTMLElement): boolean {
  return /^(\d+|[a-z]|[ivx]+)[.)]$/i.test(paragraph.dataset.marker ?? '')
}
