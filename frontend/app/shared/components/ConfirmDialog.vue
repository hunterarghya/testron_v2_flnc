<!-- Every destructive action asks first, naming the object and the consequence
     (screens.md §0.1). With `typedConfirmation`, the exact text must be typed. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  title: string
  description: string
  confirmLabel: string
  danger?: boolean
  // e.g. the student's name for "Delete permanently"
  typedConfirmation?: string
  pending?: boolean
}>()
const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ confirm: [typed: string] }>()

const typed = ref('')
watch(open, () => {
  typed.value = ''
})
const canConfirm = computed(
  () => !props.typedConfirmation || typed.value.trim() === props.typedConfirmation,
)
</script>

<template>
  <UModal v-model:open="open" :title="title" :description="description">
    <template v-if="typedConfirmation" #body>
      <UFormField :label="`Type ${typedConfirmation} to confirm`">
        <UInput v-model="typed" class="w-full" autocomplete="off" />
      </UFormField>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton
          :label="confirmLabel"
          :color="danger ? 'error' : 'primary'"
          :disabled="!canConfirm"
          :loading="pending"
          @click="emit('confirm', typed)"
        />
      </div>
    </template>
  </UModal>
</template>
