// Images into the editor (editor_content_spec.md §5.1): checked (type, size), shrunk if huge
// (phone photos), shown at once as a placeholder with a local preview, uploaded straight to
// storage, then swapped for the real image. A failed upload offers Retry or Remove.
import type { Editor } from '@tiptap/core'
import { type ApiProblem, toProblem } from '~/api/problems'
import { imageProblem, uploadImage } from '~/api/uploads'
import { IMAGE_UPLOAD } from '~/shared/components/rich-content/convert'

const LARGEST_SIDE = 4000
const SHRUNK_SIDE = 2560
const QUALITY = 0.9

// Files waiting to (re)upload, by placeholder id; they live only in this page
const waiting = new Map<string, File>()
let nextId = 0

export type Notify = (problem: ApiProblem) => void

export function startUpload(editor: Editor, file: File, notify: Notify): void {
  const problem = imageProblem(file)
  if (problem) {
    notify(problem)
    return
  }
  nextId += 1
  const uploadId = `upload-${nextId}`
  waiting.set(uploadId, file)
  editor.chain().focus().insertContent({ type: IMAGE_UPLOAD, attrs: { uploadId, previewUrl: URL.createObjectURL(file) } }).run()
  void upload(editor, uploadId, notify)
}

export async function upload(editor: Editor, uploadId: string, notify: Notify): Promise<void> {
  const original = waiting.get(uploadId)
  if (!original) return
  setPlaceholder(editor, uploadId, { failed: false })
  try {
    const { file, width, height } = await prepare(original)
    const uploaded = await uploadImage(file)
    replacePlaceholder(editor, uploadId, { provider: 'imagekit', fileId: uploaded.fileId, src: uploaded.url, width, height, size: 'M', alt: '', caption: '' })
    waiting.delete(uploadId)
  }
  catch (caught) {
    setPlaceholder(editor, uploadId, { failed: true })
    notify(toProblem(caught))
  }
}

export function forget(uploadId: string): void {
  waiting.delete(uploadId)
}

function findPlaceholder(editor: Editor, uploadId: string): { pos: number, size: number } | null {
  let found: { pos: number, size: number } | null = null
  editor.state.doc.descendants((node, pos) => {
    if (node.type.name === IMAGE_UPLOAD && node.attrs.uploadId === uploadId) found = { pos, size: node.nodeSize }
    return !found
  })
  return found
}

function setPlaceholder(editor: Editor, uploadId: string, attrs: Record<string, unknown>): void {
  const at = findPlaceholder(editor, uploadId)
  if (at) editor.view.dispatch(editor.state.tr.setNodeMarkup(at.pos, undefined, { ...editor.state.doc.nodeAt(at.pos)!.attrs, ...attrs }))
}

function replacePlaceholder(editor: Editor, uploadId: string, attrs: Record<string, unknown>): void {
  const at = findPlaceholder(editor, uploadId)
  // Removed while uploading: the file stays in storage, unused (backlog O-01 sweeps those)
  if (!at) return
  const image = editor.schema.nodes.image!.create(attrs)
  editor.view.dispatch(editor.state.tr.replaceWith(at.pos, at.pos + at.size, image))
}

/** The original pixel size, and a smaller copy when a side is over 4,000 px. */
async function prepare(file: File): Promise<{ file: File, width: number, height: number }> {
  const bitmap = await createImageBitmap(file)
  const { width, height } = bitmap
  const largest = Math.max(width, height)
  if (largest <= LARGEST_SIDE) {
    bitmap.close()
    return { file, width, height }
  }
  const scale = SHRUNK_SIDE / largest
  const canvas = new OffscreenCanvas(Math.round(width * scale), Math.round(height * scale))
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  bitmap.close()
  const type = file.type === 'image/png' ? 'image/png' : 'image/jpeg'
  const blob = await canvas.convertToBlob({ type, quality: QUALITY })
  return { file: new File([blob], file.name, { type }), width: canvas.width, height: canvas.height }
}
