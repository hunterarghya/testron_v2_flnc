<!-- T-10 ⚑: each time a student left the test, when they came back, and whether it cost a
     warning. Device changes are listed but never counted. -->
<script setup lang="ts">
import { watch } from 'vue'
import { listIntegrityEvents } from '~/features/assignments/composables/monitorApi'
import ErrorState from '~/shared/components/ErrorState.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { eventText } from '~/shared/utils/result-text'

const props = defineProps<{ attemptId: string | null, name: string }>()
const open = defineModel<boolean>('open', { required: true })

const events = useApiData(() => listIntegrityEvents(props.attemptId ?? ''))

watch(() => [open.value, props.attemptId], () => {
  if (open.value && props.attemptId) void events.refresh()
})
</script>

<template>
  <USlideover v-model:open="open" :title="`${name}: left the test`">
    <template #body>
      <ErrorState v-if="events.error.value" :problem="events.error.value" @retry="events.refresh" />
      <p v-else-if="events.data.value?.length === 0" class="text-sm text-muted">
        Never left the test.
      </p>
      <ul v-else class="space-y-2 text-sm">
        <li v-for="event in events.data.value ?? []" :key="event.left_at" class="flex items-center gap-2">
          <UIcon :name="event.counted ? 'i-lucide-flag' : 'i-lucide-circle'" class="size-4" :class="event.counted ? 'text-warning' : 'text-muted'" />
          {{ eventText(event) }}
        </li>
      </ul>
    </template>
  </USlideover>
</template>
