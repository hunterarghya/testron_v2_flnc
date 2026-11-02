// Put the cursor in a question's text, e.g. right after adding it. Its rich field loads a moment
// after the block appears, so this tries for a short while.
const TRIES = 30

export function focusQuestion(questionId: string, tries = TRIES): void {
  const field = document.querySelector<HTMLElement>(`#question-${questionId} [contenteditable="true"]`)
  if (field) field.focus()
  else if (tries > 0) requestAnimationFrame(() => focusQuestion(questionId, tries - 1))
}
