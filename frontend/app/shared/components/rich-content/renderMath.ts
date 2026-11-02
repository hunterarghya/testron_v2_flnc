// Equations, drawn by KaTeX (editor_content_spec.md §6). The single documented exception to "no
// raw HTML": KaTeX builds the HTML from a LaTeX string alone, with `trust: false`, so commands
// such as \href, \url and \includegraphics are refused and shown as errors, never as links.
import katex from 'katex'

const OPTIONS = { throwOnError: false, trust: false, strict: 'ignore', maxSize: 10, maxExpand: 200 } as const

export function renderMath(target: HTMLElement, latex: string, display: boolean): void {
  target.innerHTML = katex.renderToString(latex, { ...OPTIONS, displayMode: display })
}
