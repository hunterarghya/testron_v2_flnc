// Put the cursor in a question's text, e.g. right after adding it. Its rich field loads a moment
// after the block appears, so this tries for a short while.
const TRIES = 30

export function focusQuestion(questionId: string): void {
  focusField(`#question-${questionId} [contenteditable="true"]`)
}

/** One option's text: after Enter adds it, or Backspace removes the one after it. */
export function focusOption(questionId: string, index: number): void {
  focusField(`#question-${questionId} [data-option="${index}"] [contenteditable="true"]`)
}

function focusField(selector: string, tries = TRIES): void {
  const field = document.querySelector<HTMLElement>(selector)
  if (field) field.focus()
  else if (tries > 0) requestAnimationFrame(() => focusField(selector, tries - 1))
}
