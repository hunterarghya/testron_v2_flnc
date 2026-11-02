// Every call the test editor makes (api_contract.md §2.5). Changes carry the revision they
// are based on; the save queue supplies it.
import { api, unwrap } from '~/api/client'
import type { QuestionType, SectionPatch, TestDocument, TestPatch } from '~/api/types'
import type { QuestionBody } from '~/features/editor/utils/question-body'

export type SavePayload
  = | { kind: 'question', id: string, body: QuestionBody }
    | { kind: 'test', body: Omit<TestPatch, 'revision'> }
    | { kind: 'section', id: string, body: Omit<SectionPatch, 'revision'> }

export function getTest(testId: string): Promise<TestDocument> {
  return unwrap(api.GET('/api/v1/admin/tests/{test_id}', { params: { path: { test_id: testId } } }))
}

/** One keyed save: the whole question, the test's title/instructions, or a section. */
export function sendSave(testId: string, payload: SavePayload, revision: number) {
  switch (payload.kind) {
    case 'question':
      return unwrap(api.PATCH('/api/v1/admin/questions/{question_id}', {
        params: { path: { question_id: payload.id } },
        body: { ...payload.body, revision },
      }))
    case 'section':
      return unwrap(api.PATCH('/api/v1/admin/sections/{section_id}', {
        params: { path: { section_id: payload.id } },
        body: { ...payload.body, revision },
      }))
    default:
      return unwrap(api.PATCH('/api/v1/admin/tests/{test_id}', {
        params: { path: { test_id: testId } },
        body: { ...payload.body, revision },
      }))
  }
}

export function addQuestion(testId: string, revision: number, sectionId: string, afterId: string | null, type: QuestionType) {
  return unwrap(api.POST('/api/v1/admin/tests/{test_id}/questions', {
    params: { path: { test_id: testId } },
    body: { revision, section_id: sectionId, after_question_id: afterId, type },
  }))
}

export function deleteQuestion(questionId: string, revision: number) {
  return unwrap(api.DELETE('/api/v1/admin/questions/{question_id}', {
    params: { path: { question_id: questionId }, query: { revision } },
  }))
}

export function duplicateQuestion(questionId: string, revision: number) {
  return unwrap(api.POST('/api/v1/admin/questions/{question_id}/duplicate', {
    params: { path: { question_id: questionId } },
    body: { revision },
  }))
}

export function restructure(testId: string, revision: number, sections: { id: string, question_ids: string[] }[]) {
  return unwrap(api.PUT('/api/v1/admin/tests/{test_id}/structure', {
    params: { path: { test_id: testId } },
    body: { revision, sections },
  }))
}

export function addSection(testId: string, revision: number, afterId: string | null) {
  return unwrap(api.POST('/api/v1/admin/tests/{test_id}/sections', {
    params: { path: { test_id: testId } },
    body: { revision, after_section_id: afterId, title: '', duration_s: null },
  }))
}

export function deleteSection(sectionId: string, revision: number, questions: 'move_to_previous' | 'delete' | null) {
  return unwrap(api.DELETE('/api/v1/admin/sections/{section_id}', {
    params: { path: { section_id: sectionId }, query: { revision, questions } },
  }))
}

export function suggestTags(kind: 'CHAPTER' | 'TOPIC', typed: string): Promise<string[]> {
  return unwrap(api.GET('/api/v1/admin/tags/suggest', { params: { query: { kind, q: typed } } }))
    .then(tags => tags.map(tag => tag.name))
}
