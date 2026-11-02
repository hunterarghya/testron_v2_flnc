<!-- T-19 Defaults: what new tests start with (T-04). Existing tests keep their own settings. -->
<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import type { AppSettings, AppSettingsChanges } from '~/api/types'
import { useSubmit } from '~/shared/composables/useSubmit'
import { fieldErrors } from '~/shared/utils/form-errors'
import { DISPLAY_TIME_ZONE } from '~/shared/utils/time'

const props = defineProps<{
  settings: AppSettings
  save: (changes: AppSettingsChanges) => Promise<AppSettings>
}>()

const ACTIONS = [
  { value: 'AUTO_SUBMIT', label: 'Submit the test', description: 'The test ends and counts as usual.' },
  { value: 'DISQUALIFY', label: 'Disqualify', description: 'The test ends and is left out of results and ranks unless you override it.' },
]

const toast = useToast()
const form = reactive({ marks: '', negative: '', grace: 0, warnings: 0, action: 'AUTO_SUBMIT' as AppSettings['default_integrity_action'] })
const saving = useSubmit(props.save)
const errors = computed(() => fieldErrors(saving.problem.value))

watch(() => props.settings, (settings) => {
  form.marks = settings.default_marks
  form.negative = settings.default_negative_marks
  form.grace = settings.default_integrity_grace_s
  form.warnings = settings.default_integrity_max_warnings
  form.action = settings.default_integrity_action
}, { immediate: true })

async function onSave(): Promise<void> {
  const saved = await saving.submit({
    // Marks go as decimal strings, never floats (CLAUDE.md rule 7)
    default_marks: form.marks.trim(),
    default_negative_marks: form.negative.trim(),
    default_integrity_grace_s: form.grace,
    default_integrity_max_warnings: form.warnings,
    default_integrity_action: form.action,
  })
  if (saved) {
    toast.add({ title: 'Defaults saved', description: 'New tests start with these.', color: 'success' })
  }
}
</script>

<template>
  <UCard class="max-w-xl">
    <form class="space-y-4" @submit.prevent="onSave">
      <UAlert v-if="saving.problem.value && !Object.keys(errors).length" color="error" variant="subtle" :title="problemMessage(saving.problem.value)" />
      <div class="grid gap-4 sm:grid-cols-2">
        <UFormField label="Marks for a right answer" :error="errors.default_marks">
          <UInput v-model="form.marks" inputmode="decimal" class="w-full" required />
        </UFormField>
        <UFormField label="Marks lost for a wrong answer" :error="errors.default_negative_marks">
          <UInput v-model="form.negative" inputmode="decimal" class="w-full" required />
        </UFormField>
        <UFormField label="Grace before a warning (seconds)" help="0 to 60" :error="errors.default_integrity_grace_s">
          <UInputNumber v-model="form.grace" :min="0" :max="60" class="w-full" />
        </UFormField>
        <UFormField label="Warnings allowed" help="1 to 20" :error="errors.default_integrity_max_warnings">
          <UInputNumber v-model="form.warnings" :min="1" :max="20" class="w-full" />
        </UFormField>
      </div>
      <UFormField label="After the last warning" :error="errors.default_integrity_action">
        <URadioGroup v-model="form.action" :items="ACTIONS" />
      </UFormField>
      <UFormField label="Time zone">
        <p class="text-muted">{{ DISPLAY_TIME_ZONE }}</p>
      </UFormField>
      <UButton type="submit" label="Save defaults" :loading="saving.pending.value" />
    </form>
  </UCard>
</template>
