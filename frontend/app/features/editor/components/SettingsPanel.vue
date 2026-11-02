<!-- T-04 Test Settings (right panel): timing, order, marking defaults and integrity. Changes save
     ~0.6 s after the last one. Leaving "Sectioned" asks first: the sections merge, questions keep
     their order. Every test runs fullscreen; only the reaction to leaving it is set here. -->
<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { TestDocument, TestPatch } from '~/api/types'
import { useEditorContext } from '~/features/editor/composables/editorContext'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import { formatDuration } from '~/shared/utils/time'

type Kind = TestDocument['settings']['timing']['kind']
const SAVE_DELAY_MS = 600
const KINDS = [
  { value: 'TOTAL', label: 'Total timer', description: 'One clock for the whole test.' },
  { value: 'PER_QUESTION', label: 'Per question', description: 'Each question has its own time (override it on a question).' },
  { value: 'SECTIONED', label: 'Sectioned', description: 'Each section has its own time, set on the section.' },
]
const ACTIONS = [{ label: 'Auto-submit', value: 'AUTO_SUBMIT' }, { label: 'Disqualify', value: 'DISQUALIFY' }]

const open = defineModel<boolean>('open', { required: true })
const { editor, actions } = useEditorContext()
const doc = computed(() => editor.doc.value!)
const form = reactive({ kind: 'TOTAL' as Kind, minutes: 60, questionSeconds: 45, allowReturn: false, shuffleQuestions: false, shuffleOptions: false, marks: '', negative: '', grace: 5, warnings: 3, action: 'AUTO_SUBMIT' as 'AUTO_SUBMIT' | 'DISQUALIFY' })
const confirmingMerge = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined

watch(() => doc.value.settings, (settings) => {
  const timing = settings.timing
  Object.assign(form, {
    kind: timing.kind,
    minutes: timing.kind === 'TOTAL' ? Math.round(timing.duration_s / 60) : form.minutes,
    questionSeconds: timing.kind === 'PER_QUESTION' ? timing.default_question_s : form.questionSeconds,
    allowReturn: timing.kind === 'SECTIONED' ? timing.allow_return : false,
    shuffleQuestions: settings.shuffle_questions,
    shuffleOptions: settings.shuffle_options,
    marks: settings.marking.marks,
    negative: settings.marking.negative_marks,
    grace: settings.integrity.grace_s,
    warnings: settings.integrity.max_warnings,
    action: settings.integrity.action,
  })
}, { immediate: true })

function timingPatch(): NonNullable<TestPatch['settings']>['timing'] {
  // A new kind takes the server's starting values (ADR-062); the same kind sends its own
  if (form.kind !== doc.value.settings.timing.kind) return { kind: form.kind }
  if (form.kind === 'TOTAL') return { kind: 'TOTAL', duration_s: form.minutes * 60 }
  if (form.kind === 'PER_QUESTION') return { kind: 'PER_QUESTION', default_question_s: form.questionSeconds }
  return { kind: 'SECTIONED', allow_return: form.allowReturn }
}

function save(): void {
  clearTimeout(timer)
  timer = undefined
  void actions.saveSettings({
    timing: timingPatch(),
    shuffle_questions: form.shuffleQuestions,
    shuffle_options: form.shuffleOptions,
    marking: { marks: form.marks.trim(), negative_marks: form.negative.trim() },
    integrity: { grace_s: form.grace, max_warnings: form.warnings, action: form.action },
  })
}

function changed(): void {
  clearTimeout(timer)
  timer = setTimeout(save, SAVE_DELAY_MS)
}

function onKind(value: string): void {
  const kind = value as Kind
  const leaving = doc.value.settings.timing.kind === 'SECTIONED' && kind !== 'SECTIONED'
  form.kind = kind
  if (leaving && doc.value.sections.length > 1) confirmingMerge.value = true
  else save()
}

let mergeConfirmed = false

function confirmMerge(): void {
  mergeConfirmed = true
  confirmingMerge.value = false
  save()
}

// Closed without confirming: the test stays sectioned
watch(confirmingMerge, (isOpen) => {
  if (!isOpen && !mergeConfirmed) form.kind = 'SECTIONED'
  if (!isOpen) mergeConfirmed = false
})

watch(open, (isOpen) => {
  if (!isOpen && timer) save()
})
</script>

<template>
  <USlideover v-model:open="open" title="Settings" description="These are defaults. Each assignment can override them.">
    <template #body>
      <div class="space-y-6">
        <section class="space-y-3">
          <h3 class="text-sm font-semibold uppercase text-muted">Timing structure</h3>
          <URadioGroup :model-value="form.kind" :items="KINDS" :disabled="editor.readOnly.value" @update:model-value="onKind" />
          <UFormField v-if="form.kind === 'TOTAL'" label="Duration (minutes)">
            <UInputNumber v-model="form.minutes" :min="1" :max="1440" @update:model-value="changed" />
          </UFormField>
          <UFormField v-else-if="form.kind === 'PER_QUESTION'" label="Default per question (seconds)">
            <UInputNumber v-model="form.questionSeconds" :min="5" :max="3600" @update:model-value="changed" />
          </UFormField>
          <UCheckbox v-else v-model="form.allowReturn" label="Allow returning to a section while its time remains" @update:model-value="changed" />
          <p v-if="form.kind !== 'TOTAL'" class="text-sm text-muted">
            Total time: {{ doc.totals.duration_s === null ? 'not set yet' : formatDuration(doc.totals.duration_s) }}
          </p>
        </section>
        <section class="space-y-2">
          <h3 class="text-sm font-semibold uppercase text-muted">Order</h3>
          <USwitch v-model="form.shuffleQuestions" label="Shuffle questions (within sections)" @update:model-value="changed" />
          <USwitch v-model="form.shuffleOptions" label="Shuffle options" @update:model-value="changed" />
        </section>
        <section class="space-y-2">
          <h3 class="text-sm font-semibold uppercase text-muted">Marking defaults</h3>
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Correct (+)"><UInput v-model="form.marks" inputmode="decimal" @update:model-value="changed" /></UFormField>
            <UFormField label="Wrong (−)"><UInput v-model="form.negative" inputmode="decimal" @update:model-value="changed" /></UFormField>
          </div>
          <p class="text-sm text-muted">Any question can override these in the document.</p>
        </section>
        <section class="space-y-2">
          <h3 class="text-sm font-semibold uppercase text-muted">Integrity (tests always run fullscreen)</h3>
          <UFormField label="Grace period (seconds)"><UInputNumber v-model="form.grace" :min="0" :max="60" @update:model-value="changed" /></UFormField>
          <UFormField label="Max warnings"><UInputNumber v-model="form.warnings" :min="1" :max="20" @update:model-value="changed" /></UFormField>
          <UFormField label="When exceeded"><USelect v-model="form.action" :items="ACTIONS" class="w-40" @update:model-value="changed" /></UFormField>
        </section>
      </div>
      <ConfirmDialog
        v-model:open="confirmingMerge"
        title="Remove sections?"
        description="All questions move into one section, in the same order. Section names and durations are dropped."
        confirm-label="Remove sections"
        @confirm="confirmMerge"
      />
    </template>
  </USlideover>
</template>
