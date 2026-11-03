<!-- T-08 ⋯ Edit settings: the wizard's step ③ fields and the name. Before the start
     everything here can change; after it, only the name and results (`editable_fields`). -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { ApiProblem } from '~/api/problems'
import type { AssignmentChanges, AssignmentDetail } from '~/api/types'
import GateFields from '~/features/assignments/components/when/GateFields.vue'
import ResultsFields from '~/features/assignments/components/when/ResultsFields.vue'
import WindowFields from '~/features/assignments/components/when/WindowFields.vue'
import { type WhenForm, toChanges, whenFormFrom } from '~/features/assignments/utils/when-form'
import { fieldErrors } from '~/shared/utils/form-errors'

const props = defineProps<{
  detail: AssignmentDetail
  save: (changes: AssignmentChanges) => Promise<AssignmentDetail | undefined>
  pending: boolean
  problem: ApiProblem | null
}>()
const open = defineModel<boolean>('open', { required: true })

const form = ref<WhenForm>(whenFormFrom(props.detail))
const title = ref(props.detail.title)
const editable = computed(() => props.detail.editable_fields)
const errors = computed(() => fieldErrors(props.problem))

watch(open, (isOpen) => {
  if (isOpen) {
    form.value = whenFormFrom(props.detail)
    title.value = props.detail.title
  }
})

async function submit(): Promise<void> {
  if (await props.save(toChanges(form.value, title.value, editable.value))) open.value = false
}
</script>

<template>
  <UModal v-model:open="open" title="Edit settings" :ui="{ content: 'max-w-3xl' }">
    <template #body>
      <div class="space-y-8">
        <UFormField label="Name" :error="errors.title">
          <UInput v-model="title" class="w-full" :maxlength="200" />
        </UFormField>
        <template v-if="editable.includes('window')">
          <WindowFields v-model="form" :errors="errors" />
          <GateFields v-model="form" :errors="errors" :with-password="false" />
        </template>
        <ResultsFields v-model="form" :errors="errors" :with-integrity="editable.includes('integrity')" />
        <UAlert v-if="problem" color="error" variant="subtle" :title="problemMessage(problem)" />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton label="Save" :loading="pending" @click="submit" />
      </div>
    </template>
  </UModal>
</template>
