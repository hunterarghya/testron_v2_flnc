import { describe, expect, it } from 'vitest'
import type { KeyedPaper } from '~/api/types'
import { collectCss, escapeHtml, htmlDocument } from '~/features/exports/utils/html-document'
import { keyAsQuestions } from '~/features/exports/utils/key-questions'
import {
  answerKeyName,
  answerSheetName,
  answerSheetsZipName,
  fileName,
  indiaDate,
  MAX_NAME_LENGTH,
} from '~/shared/utils/file-names'

// 20:00 UTC on 11 Nov is already 12 Nov in India
const LATE = new Date('2026-11-11T20:00:00Z')

describe('export file names (domain_model.md §6.6)', () => {
  it('uses the India date', () => {
    expect(indiaDate(LATE)).toBe('2026-11-12')
  })

  it('names each kind of file', () => {
    expect(answerSheetName('Mou Ghosh', 'Cell Biology', 1, LATE)).toBe('Mou Ghosh - Cell Biology - 2026-11-12.html')
    expect(answerSheetName('Mou Ghosh', 'Cell Biology', 2, LATE)).toBe('Mou Ghosh - Cell Biology - 2026-11-12 - Take 2.html')
    expect(answerKeyName('Cell Biology', LATE)).toBe('Cell Biology - Answer Key - 2026-11-12.html')
    expect(answerSheetsZipName('Cell Biology', LATE)).toBe('Cell Biology - 2026-11-12 - Answer Sheets.zip')
  })

  it('removes characters file systems refuse and keeps the extension under the cap', () => {
    expect(fileName(['Cell: "Biology"?', 'রিনা\u0007'], 'html')).toBe('Cell Biology - রিনা.html')
    const long = fileName(['x'.repeat(400)], 'zip')
    expect(long).toHaveLength(MAX_NAME_LENGTH)
    expect(long.endsWith('.zip')).toBe(true)
  })
})

function sheet(rules: string[], throws = false): CSSStyleSheet {
  return { get cssRules() {
    if (throws) throw new DOMException('cross-origin', 'SecurityError')
    return rules.map(cssText => ({ cssText }))
  } } as unknown as CSSStyleSheet
}

describe('the self-contained HTML file', () => {
  it('keeps the page styles but not their font files', () => {
    const css = collectCss([sheet(['.a{color:red}', '@font-face{font-family:X;src:url(/x.woff2)}']), sheet([], true)])
    expect(css).toBe('.a{color:red}')
  })

  it('wraps the body with an escaped title and the styles', () => {
    const html = htmlDocument('Mou <Take 2>', '<p>hi</p>', '.a{}')
    expect(html.startsWith('<!doctype html>')).toBe(true)
    expect(html).toContain('<title>Mou &lt;Take 2&gt;</title>')
    expect(html).toContain('<main><p>hi</p></main>')
    expect(escapeHtml('"&"')).toBe('&quot;&amp;&quot;')
  })
})

describe('the answer key as questions', () => {
  it('numbers the questions and carries their answers and solutions', () => {
    const doc = { type: 'doc', content: [] }
    const keyed: KeyedPaper = {
      version: 2,
      paper: { sections: [{ questions: [
        { id: 'q1', type: 'MCQ', stem: doc, marks: '4.00', negative_marks: '1.00', options: [{ id: 'o1', content: doc }, { id: 'o2', content: doc }] },
        { id: 'q2', type: 'NUMERICAL', stem: doc, marks: '4.00', negative_marks: '0.00' },
      ] }] },
      entries: { q1: { correct_option_ids: ['o2'] }, q2: { answer: '46', tolerance: '0.5' } },
      solutions: { q2: doc },
    }

    const [mcq, numerical] = keyAsQuestions(keyed)

    expect(mcq).toMatchObject({ number: 1, correct_answer: { option_ids: ['o2'] }, solution: null })
    expect(mcq!.options.map(o => o.label)).toEqual(['A', 'B'])
    expect(numerical).toMatchObject({ number: 2, correct_answer: { value: '46', tolerance: '0.5' }, solution: doc })
  })
})
