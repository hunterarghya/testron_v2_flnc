// What happens when content is pasted or dropped into a rich field (editor_content_spec.md §4.3,
// §5.1): HTML is cleaned first, then read through the schema; image files and embedded images
// are uploaded; remote images can't be fetched, so the teacher is told to upload them.
import type { Editor } from '@tiptap/core'
import { ApiProblem } from '~/api/problems'
import { cleanText } from '~/shared/components/rich-content/clean-text'
import { cleanPastedHtml } from '~/shared/components/rich-content/paste'
import { type Notify, startUpload } from '~/shared/components/rich-content/uploads'

const IMAGE = /^image\//

function dataUrlToFile(dataUrl: string, index: number): File {
  const [header, body] = dataUrl.split(',', 2)
  const type = /data:([^;]+)/.exec(header ?? '')?.[1] ?? 'image/png'
  const bytes = Uint8Array.from(atob(body ?? ''), character => character.charCodeAt(0))
  return new File([bytes], `pasted-${index + 1}.${type.split('/')[1] ?? 'png'}`, { type })
}

function remoteNotice(count: number): ApiProblem {
  const detail = `${count} image${count === 1 ? '' : 's'} couldn't be copied, so upload ${count === 1 ? 'it' : 'them'}`
  return new ApiProblem({ status: 0, code: 'image_not_copied', detail })
}

export function usePaste(getEditor: () => Editor | null, notify: Notify) {
  function uploadFiles(editor: Editor, files: File[]): void {
    files.filter(file => IMAGE.test(file.type)).forEach(file => startUpload(editor, file, notify))
  }

  const editorProps = {
    transformPastedHTML(html: string): string {
      const cleaned = cleanPastedHtml(html)
      if (cleaned.remoteImages) notify(remoteNotice(cleaned.remoteImages))
      const editor = getEditor()
      // After the text lands, so the images follow it
      if (editor && cleaned.dataImages.length) {
        setTimeout(() => uploadFiles(editor, cleaned.dataImages.map(dataUrlToFile)))
      }
      return cleaned.html
    },
    transformPastedText: (text: string) => cleanText(text),
    handlePaste(_view: unknown, event: ClipboardEvent): boolean {
      const files = [...(event.clipboardData?.files ?? [])]
      const editor = getEditor()
      // Only a picture (a screenshot): upload it. With HTML too, the HTML path handles it.
      if (!editor || !files.length || event.clipboardData?.getData('text/html')) return false
      uploadFiles(editor, files)
      return true
    },
    handleDrop(_view: unknown, event: DragEvent): boolean {
      const files = [...(event.dataTransfer?.files ?? [])]
      const editor = getEditor()
      if (!editor || !files.some(file => IMAGE.test(file.type))) return false
      uploadFiles(editor, files)
      return true
    },
  }

  return { editorProps, uploadFiles }
}
