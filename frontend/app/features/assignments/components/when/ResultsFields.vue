<!-- T-07 ③ Integrity (always fullscreen) and Results: manual or automatic publication [H-1]. -->
<script setup lang="ts">
import type { Publication } from '~/api/types'
import type { DelayUnit, WhenForm } from '~/features/assignments/utils/when-form'

withDefaults(defineProps<{ errors: Record<string, string>, withIntegrity?: boolean }>(), { withIntegrity: true })
const form = defineModel<WhenForm>({ required: true })

const ACTIONS = [
  { value: 'AUTO_SUBMIT', label: 'Auto-submit' },
  { value: 'DISQUALIFY', label: 'Disqualify' },
]
const MODES: { value: Publication['mode'], label: string }[] = [
  { value: 'MANUAL', label: 'I publish manually' },
  { value: 'AUTO_IMMEDIATE', label: 'Auto-publish immediately when each student finishes' },
  { value: 'AUTO_DELAYED', label: 'Auto-publish some time after the test ends' },
]
const UNITS: DelayUnit[] = ['minutes', 'hours', 'days']
const CONTENTS = [
  { value: 'SCORE_ONLY', label: 'Score only' },
  { value: 'ANSWER_REVIEW', label: 'Score and answer review' },
]

function setIntegrity(changes: Partial<WhenForm['integrity']>): void {
  form.value = { ...form.value, integrity: { ...form.value.integrity, ...changes } }
}

function setPublication(changes: Partial<WhenForm['publication']>): void {
  form.value = { ...form.value, publication: { ...form.value.publication, ...changes } }
}
</script>

<template>
  <div class="space-y-6">
    <fieldset v-if="withIntegrity" class="space-y-3">
      <legend class="text-sm font-medium">
        Integrity (tests always run fullscreen)
      </legend>
      <div class="flex flex-wrap gap-3">
        <UFormField label="Warnings allowed" :error="errors['integrity.max_warnings']">
          <UInputNumber :model-value="form.integrity.max_warnings" :min="1" :max="20" @update:model-value="v => setIntegrity({ max_warnings: v ?? 1 })" />
        </UFormField>
        <UFormField label="Grace (seconds)" :error="errors['integrity.grace_s']">
          <UInputNumber :model-value="form.integrity.grace_s" :min="0" :max="60" @update:model-value="v => setIntegrity({ grace_s: v ?? 0 })" />
        </UFormField>
        <UFormField label="When exceeded">
          <USelect
            :model-value="form.integrity.action"
            :items="ACTIONS"
            class="w-40"
            @update:model-value="v => setIntegrity({ action: v as WhenForm['integrity']['action'] })"
          />
        </UFormField>
      </div>
    </fieldset>
    <fieldset class="space-y-3">
      <legend class="text-sm font-medium">
        Results
      </legend>
      <URadioGroup
        :model-value="form.publication.mode"
        :items="MODES"
        @update:model-value="v => setPublication({ mode: v as Publication['mode'] })"
      />
      <div v-if="form.publication.mode === 'AUTO_DELAYED'" class="flex flex-wrap items-end gap-2">
        <UFormField label="After" :error="errors['publication.delay_s']">
          <UInputNumber :model-value="form.delayValue" :min="1" @update:model-value="v => form = { ...form, delayValue: v ?? 1 }" />
        </UFormField>
        <USelect :model-value="form.delayUnit" :items="UNITS" class="w-32" @update:model-value="v => form = { ...form, delayUnit: v as DelayUnit }" />
      </div>
      <USelect
        :model-value="form.publication.content"
        :items="CONTENTS"
        class="w-64"
        aria-label="What students see"
        @update:model-value="v => setPublication({ content: v as Publication['content'], show_paper: v === 'ANSWER_REVIEW' })"
      />
      <div class="flex flex-wrap gap-4">
        <UCheckbox :model-value="form.publication.show_paper" label="Show the paper" @update:model-value="v => setPublication({ show_paper: Boolean(v) })" />
        <UCheckbox :model-value="form.publication.show_solutions" label="Show solutions" @update:model-value="v => setPublication({ show_solutions: Boolean(v) })" />
        <UCheckbox :model-value="form.publication.show_rank_and_stats" label="Show rank and class stats" @update:model-value="v => setPublication({ show_rank_and_stats: Boolean(v) })" />
      </div>
    </fieldset>
  </div>
</template>
