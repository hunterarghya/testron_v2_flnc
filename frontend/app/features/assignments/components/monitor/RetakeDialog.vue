<!-- D-02 Unlock retake: one more sitting each for the selected students, on its own clock. A
     student who missed the test gets a late first sitting. -->
<script setup lang="ts">
import { problemMessage } from '~/api/problem-messages'
import { grantRetakes } from '~/features/assignments/composables/monitorApi'
import { useSubmit } from '~/shared/composables/useSubmit'

const props = defineProps<{ assignmentId: string, students: { id: string, name: string }[] }>()
const emit = defineEmits<{ done: [granted: number] }>()
const open = defineModel<boolean>('open', { required: true })

const granting = useSubmit(grantRetakes)

async function grant(): Promise<void> {
  const result = await granting.submit(props.assignmentId, props.students.map(s => s.id))
  if (!result) return
  open.value = false
  emit('done', result.succeeded.length)
}
</script>

<template>
  <UModal v-model:open="open" title="Unlock a retake?">
    <template #body>
      <div class="space-y-3 text-sm">
        <p>{{ students.map(s => s.name).join(', ') }}</p>
        <p>Each gets one more attempt, with the full time. Retakes are separate results labelled "Take N".</p>
        <UAlert v-if="granting.problem.value" color="error" variant="subtle" :title="problemMessage(granting.problem.value)" />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="outline" @click="open = false" />
        <UButton label="Unlock retake" :loading="granting.pending.value" @click="grant" />
      </div>
    </template>
  </UModal>
</template>
