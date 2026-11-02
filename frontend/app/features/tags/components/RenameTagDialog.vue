<!-- T-18 Rename: fixes the label everywhere. Renaming onto another tag's name asks first,
     then merges the two: "Merge 'Genetcs' (2 questions) into 'Genetics' (25)?" -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { TagUsage } from '~/api/types'
import { type MergeTarget, mergeTarget } from '~/features/tags/composables/useTags'
import { fieldErrors } from '~/shared/utils/form-errors'

const props = defineProps<{
  tag: TagUsage | null
  rename: (tagId: string, name: string, merge: boolean) => Promise<void>
}>()
const open = defineModel<boolean>('open', { required: true })

const toast = useToast()
const name = ref('')
const error = ref<string>()
const merging = ref<MergeTarget | null>(null)
const pending = ref(false)
const title = computed(() => (merging.value ? 'Merge tags?' : `Rename ${props.tag?.name ?? ''}`))

watch(open, (isOpen) => {
  if (isOpen) {
    name.value = props.tag?.name ?? ''
    error.value = undefined
    merging.value = null
  }
})

async function save(): Promise<void> {
  const tag = props.tag
  if (!tag) {
    return
  }
  pending.value = true
  try {
    await props.rename(tag.id, name.value, merging.value !== null)
    toast.add({ title: merging.value ? `Merged into ${merging.value.name}` : 'Tag renamed', color: 'success' })
    open.value = false
  }
  catch (caught) {
    merging.value = mergeTarget(caught)
    const problem = toProblem(caught)
    error.value = merging.value ? undefined : (fieldErrors(problem).name ?? problemMessage(problem))
  }
  finally {
    pending.value = false
  }
}
</script>

<template>
  <UModal v-model:open="open" :title="title">
    <template #body>
      <p v-if="merging && tag">
        Merge <strong>{{ tag.name }}</strong> ({{ tag.question_count }} questions) into
        <strong>{{ merging.name }}</strong> ({{ merging.question_count }})?
        Every question tagged {{ tag.name }} will be tagged {{ merging.name }}.
      </p>
      <form v-else id="rename-tag" @submit.prevent="save">
        <UFormField label="New name" :error="error">
          <UInput v-model="name" class="w-full" required autofocus />
        </UFormField>
      </form>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton v-if="merging" label="Merge" :loading="pending" @click="save" />
        <UButton v-else type="submit" form="rename-tag" label="Rename" :loading="pending" />
      </div>
    </template>
  </UModal>
</template>
