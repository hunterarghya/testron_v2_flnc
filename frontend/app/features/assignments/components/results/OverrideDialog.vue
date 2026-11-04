<!-- D-09 Count a disqualified attempt [G-2]: with a required reason (kept in the audit log),
     it joins the ranking and, once published, the student sees their score. -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import { overrideDisqualification } from '~/features/assignments/composables/resultsApi'
import { useSubmit } from '~/shared/composables/useSubmit'

const props = defineProps<{ attemptId: string | null, name: string }>()
const emit = defineEmits<{ done: [] }>()
const open = defineModel<boolean>('open', { required: true })

const reason = ref('')
const overriding = useSubmit(overrideDisqualification)

watch(open, () => {
  reason.value = ''
})

async function count(): Promise<void> {
  if (!props.attemptId) return
  await overriding.submit(props.attemptId, reason.value)
  if (overriding.problem.value) return
  open.value = false
  emit('done')
}
</script>

<template>
  <UModal v-model:open="open" :title="`Count ${name}'s attempt?`" description="It joins the ranking, and once published the student sees their score.">
    <template #body>
      <UFormField label="Reason (kept in the audit log)" required>
        <UTextarea v-model="reason" :rows="2" class="w-full" />
      </UFormField>
      <UAlert v-if="overriding.problem.value" class="mt-3" color="error" variant="subtle" :title="problemMessage(overriding.problem.value)" />
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="outline" @click="open = false" />
        <UButton label="Count this attempt" :disabled="!reason.trim()" :loading="overriding.pending.value" @click="count" />
      </div>
    </template>
  </UModal>
</template>
