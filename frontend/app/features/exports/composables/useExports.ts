// The browser exports (ADR-019, frontend_spec.md §6): a sheet or the key is drawn by the same
// components as the screens into a detached element (with the app's components and plugins),
// its images decoded and fonts ready, then wrapped with the page's styles and the embedded
// fonts into one HTML file. A ZIP of many sheets is built one sheet at a time, with progress.
import { type Component, h, nextTick, ref, render } from 'vue'
import type { AnswerSheet } from '~/api/types'
import KeyDocument from '~/features/exports/components/KeyDocument.vue'
import SheetDocument from '~/features/exports/components/SheetDocument.vue'
import { collectCss, htmlDocument } from '~/features/exports/utils/html-document'
import { getAnswerKey, listAnswerSheets } from '~/shared/composables/resultDocumentsApi'
import { answerKeyName, answerSheetName, answerSheetsZipName, saveFile } from '~/shared/utils/file-names'

const HTML = 'text/html;charset=utf-8'

/** The test's title, from a sheet's label "Title — date — Take N". */
export function titleOf(sheet: AnswerSheet): string {
  return sheet.label.split(' — ')[0] ?? sheet.label
}

export function useExports() {
  const appContext = useNuxtApp().vueApp._context
  // "12 / 42" while a ZIP is being built
  const progress = ref<{ done: number, total: number } | null>(null)

  async function toHtml(title: string, component: Component, props: Record<string, unknown>): Promise<string> {
    const host = document.createElement('div')
    const node = h(component, props)
    node.appContext = appContext
    render(node, host)
    await nextTick()
    await Promise.all([...host.querySelectorAll('img')].map(img => img.decode().catch(() => undefined)))
    // Every supported browser has it; a test DOM may not
    await (document.fonts as FontFaceSet | undefined)?.ready
    // Read out, never written from data (CLAUDE.md rule 5): the sheet as the screen drew it
    const serializer = new XMLSerializer()
    const body = Array.from(host.childNodes, n => serializer.serializeToString(n)).join('')
    render(null, host)
    const { fontFaces } = await import('~/features/exports/utils/fonts')
    return htmlDocument(title, body, `${fontFaces()}\n${collectCss()}`)
  }

  function sheetHtml(sheet: AnswerSheet): Promise<string> {
    return toHtml(`${sheet.student.name} · ${sheet.label}`, SheetDocument, { sheet })
  }

  async function downloadSheet(sheet: AnswerSheet): Promise<void> {
    const html = await sheetHtml(sheet)
    saveFile(answerSheetName(sheet.student.name, titleOf(sheet), sheet.take_number), new Blob([html], { type: HTML }))
  }

  async function downloadKey(assignmentId: string, title: string): Promise<void> {
    const keyed = await getAnswerKey(assignmentId)
    const html = await toHtml(`${title} — Answer key`, KeyDocument, { keyed, title })
    saveFile(answerKeyName(title), new Blob([html], { type: HTML }))
  }

  /** The chosen attempts' sheets (all ended ones when none are chosen) in one ZIP. */
  async function downloadSheets(assignmentId: string, title: string, attemptIds: string[] = []): Promise<void> {
    const sheets = await listAnswerSheets(assignmentId, attemptIds)
    const { default: JSZip } = await import('jszip')
    const zip = new JSZip()
    progress.value = { done: 0, total: sheets.length }
    try {
      for (const sheet of sheets) {
        zip.file(answerSheetName(sheet.student.name, title, sheet.take_number), await sheetHtml(sheet))
        progress.value = { done: progress.value.done + 1, total: sheets.length }
      }
      saveFile(answerSheetsZipName(title), await zip.generateAsync({ type: 'blob' }))
    }
    finally {
      progress.value = null
    }
  }

  return { progress, downloadSheet, downloadKey, downloadSheets }
}
