// What one question save sends, and what the editor takes back from the answer
// (api_contract.md §2.5: the whole question; options replaced, kept ids stay; tags by name).
import type { EditorOption, EditorQuestion, QuestionPatch, RichDoc, Tag } from '~/api/types'
import { EMPTY_DOC } from '~/shared/utils/plain-doc'

export type QuestionBody = Omit<QuestionPatch, 'revision'>

export function questionBody(question: EditorQuestion): QuestionBody {
  const body: QuestionBody = {
    type: question.type,
    stem: question.stem,
    solution: question.solution,
    marks_override: question.marks_override,
    negative_marks_override: question.negative_marks_override,
    time_override_s: question.time_override_s,
    chapter_tags: question.chapter_tags.map(tag => tag.name),
    topic_tags: question.topic_tags.map(tag => tag.name),
  }
  if (question.type === 'NUMERICAL') {
    body.numeric_answer = question.numeric_answer
    body.numeric_tolerance = question.numeric_tolerance
    body.options = []
  }
  else {
    body.options = question.options.map(option => ({
      id: isNewOption(option) ? null : option.id,
      content: option.content,
      is_correct: option.is_correct,
    }))
  }
  return body
}

/** After a save: new options and new tags get the ids the server gave them, when the editor
 * still holds the same list (more typing since then is saved next anyway). */
export function adoptIds(local: EditorQuestion, saved: EditorQuestion): void {
  if (local.options.length === saved.options.length) {
    local.options.forEach((option, index) => {
      if (isNewOption(option)) option.id = saved.options[index]!.id
    })
  }
  local.chapter_tags = sameNames(local.chapter_tags, saved.chapter_tags) ? saved.chapter_tags : local.chapter_tags
  local.topic_tags = sameNames(local.topic_tags, saved.topic_tags) ? saved.topic_tags : local.topic_tags
}

function sameNames(a: Tag[], b: Tag[]): boolean {
  const names = (tags: Tag[]) => tags.map(tag => tag.name.trim().toLocaleLowerCase()).sort().join('\n')
  return names(a) === names(b)
}

/** "A", "B", … for option positions (they renumber as options come and go). */
export function optionLabel(index: number): string {
  return String.fromCharCode(65 + index)
}

// A new option has no id until the server gives it one; locally it has a temporary key
const NEW_PREFIX = 'new:'
let nextNew = 0

export function newOption(content: RichDoc = EMPTY_DOC): EditorOption {
  nextNew += 1
  return { id: `${NEW_PREFIX}${nextNew}`, content, is_correct: false }
}

export function isNewOption(option: EditorOption): boolean {
  return option.id.startsWith(NEW_PREFIX)
}

/** The question after a type switch (domain_model.md §3.4 invariant 3): MCQ <-> MSQ keeps the
 * options; to numerical drops them (the UI asks first); from numerical starts four empty ones. */
export function retyped(question: EditorQuestion, type: EditorQuestion['type']): void {
  if (type === 'NUMERICAL') {
    question.options = []
  }
  else if (question.type === 'NUMERICAL') {
    question.options = [newOption(), newOption(), newOption(), newOption()]
    question.numeric_answer = null
    question.numeric_tolerance = '0'
  }
  question.type = type
}
