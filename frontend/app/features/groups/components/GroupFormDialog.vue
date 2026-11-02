<!-- New group (T-16) or edit one (T-17): name and description. A name already used by another
     active group is shown under the name field. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { Group } from '~/api/types'
import { createGroup, type GroupFields, updateGroup } from '~/features/groups/composables/groupsApi'
import { useSubmit } from '~/shared/composables/useSubmit'
import { fieldErrors } from '~/shared/utils/form-errors'

const props = defineProps<{ group?: Group }>()
const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ saved: [group: Group] }>()

const name = ref('')
const description = ref('')
const saving = useSubmit((fields: GroupFields) =>
  props.group ? updateGroup(props.group.id, fields) : createGroup(fields),
)
const errors = computed(() => fieldErrors(saving.problem.value))
const otherProblem = computed(() =>
  saving.problem.value && !errors.value.name ? problemMessage(saving.problem.value) : undefined,
)

watch(open, (isOpen) => {
  if (isOpen) {
    name.value = props.group?.name ?? ''
    description.value = props.group?.description ?? ''
    saving.problem.value = null
  }
})

async function onSave(): Promise<void> {
  const saved = await saving.submit({ name: name.value, description: description.value })
  if (saved) {
    emit('saved', saved)
    open.value = false
  }
}
</script>

<template>
  <UModal v-model:open="open" :title="group ? 'Edit group' : 'New group'">
    <template #body>
      <form id="group-form" class="space-y-4" @submit.prevent="onSave">
        <UAlert v-if="otherProblem" color="error" variant="subtle" :title="otherProblem" />
        <UFormField label="Name" :error="errors.name">
          <UInput v-model="name" class="w-full" required autofocus />
        </UFormField>
        <UFormField label="Description" hint="Optional">
          <UTextarea v-model="description" class="w-full" :rows="2" />
        </UFormField>
      </form>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton type="submit" form="group-form" :label="group ? 'Save' : 'Create group'" :loading="saving.pending.value" />
      </div>
    </template>
  </UModal>
</template>
