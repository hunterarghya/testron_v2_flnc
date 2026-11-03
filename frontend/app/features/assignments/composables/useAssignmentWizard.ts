// T-07's state: the four steps' answers, the test's own settings as defaults, the audience
// list built from groups, and Create. "Assign again" starts from an earlier assignment [D-7].
import { computed, reactive, ref, shallowRef } from 'vue'
import type { AssignmentDetail, NewAssignment, TestDocument } from '~/api/types'
import {
  createAssignment,
  getAssignment,
  getTestDocument,
  previewAudience,
} from '~/features/assignments/composables/assignmentsApi'
import { type AudienceEntry, addIndividuals, mergeGroups, tickedIds } from '~/features/assignments/utils/audience'
import { type TimingEdit, timingEditFrom, toTimingOverride } from '~/features/assignments/utils/timing'
import { type WhenForm, emptyWhenForm, toPublication, toWindow, whenFormFrom } from '~/features/assignments/utils/when-form'
import { useSubmit } from '~/shared/composables/useSubmit'

export const STEPS = ['Test', 'Students', 'When & how', 'Review'] as const

export function useAssignmentWizard() {
  const step = ref(0)
  const test = shallowRef<TestDocument | null>(null)
  const title = ref('')
  const groupIds = ref<string[]>([])
  const audience = ref<AudienceEntry[]>([])
  const form = ref<WhenForm | null>(null)
  const timing = reactive<{ edit: TimingEdit | null, changed: boolean }>({ edit: null, changed: false })
  const creating = useSubmit((body: NewAssignment) => createAssignment(body))

  async function pickTest(testId: string): Promise<void> {
    const document = await getTestDocument(testId)
    test.value = document
    title.value ||= document.title
    form.value ??= emptyWhenForm(document.settings.integrity)
    timing.edit = timingEditFrom(document)
    timing.changed = false
  }

  async function pickGroups(ids: string[]): Promise<void> {
    groupIds.value = ids
    const candidates = ids.length ? await previewAudience(ids) : []
    audience.value = mergeGroups(audience.value, candidates)
  }

  function addStudents(students: { id: string, name: string }[]): void {
    audience.value = addIndividuals(audience.value, students)
  }

  /** Assign again [D-7]: the same test, groups, individuals and settings, all changeable.
   *  The password isn't copied: the teacher types a new one. */
  async function startFrom(assignmentId: string): Promise<void> {
    const earlier = await getAssignment(assignmentId)
    await pickTest(earlier.test_id)
    title.value = earlier.title
    form.value = { ...whenFormFrom(earlier), password: '', passwordConfirm: '' }
    await pickGroups(earlier.source_group_ids)
    // Everyone who sat it before, ticked; group members who were left out stay unticked
    addStudents(earlier.audience_students)
    const before = new Set(earlier.audience_students.map(student => student.id))
    audience.value = audience.value.map(entry => ({ ...entry, ticked: before.has(entry.studentId) }))
  }

  const canContinue = computed(() => [
    Boolean(test.value && title.value.trim() && !test.value.problems.length),
    tickedIds(audience.value).length > 0,
    form.value !== null,
    true,
  ][step.value])

  function payload(): NewAssignment | null {
    if (!test.value || !form.value) return null
    const when = form.value
    return {
      test_id: test.value.id,
      title: title.value,
      student_ids: tickedIds(audience.value),
      source_group_ids: groupIds.value,
      window: toWindow(when),
      gate: {
        requires_activation: when.requiresActivation,
        password: when.usePassword ? when.password : null,
        password_confirm: when.usePassword ? when.passwordConfirm : null,
      },
      timing_override: timing.changed && timing.edit ? toTimingOverride(test.value, timing.edit) : null,
      integrity: when.integrity,
      publication: toPublication(when),
    }
  }

  async function create(): Promise<AssignmentDetail | undefined> {
    const body = payload()
    return body ? creating.submit(body) : undefined
  }

  return { step, test, title, groupIds, audience, form, timing, creating, canContinue, pickTest, pickGroups, addStudents, startFrom, create }
}
