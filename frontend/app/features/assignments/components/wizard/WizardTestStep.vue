<!-- T-07 ① Test: pick a test without problems, and the name students will see. -->
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { api, unwrap } from '~/api/client'
import type { TestDocument } from '~/api/types'
import { problemMessage } from '~/api/problem-messages'
import { useApiData } from '~/shared/composables/useApiData'
import { formatDuration } from '~/shared/utils/time'

// The picker lists active tests; a coaching centre has tens, not thousands
const SHOWN = 200

const props = defineProps<{ test: TestDocument | null }>()
const title = defineModel<string>('title', { required: true })
const emit = defineEmits<{ pick: [testId: string] }>()

const tests = useApiData(() => unwrap(api.GET('/api/v1/admin/tests', {
  params: { query: { status: 'active', sort: '-updated_at', page_size: SHOWN } },
})))
const items = computed(() => (tests.data.value?.items ?? []).map(row => ({
  value: row.id,
  label: row.title,
  // Only a test without problems can be assigned (domain_model.md §3.5 #1)
  disabled: row.problem_count > 0,
  suffix: row.problem_count ? `Fix ${row.problem_count} problem${row.problem_count > 1 ? 's' : ''} first` : undefined,
})))
const testId = computed({
  get: () => props.test?.id,
  set: (id?: string) => { if (id) emit('pick', id) },
})
const facts = computed(() => {
  const test = props.test
  if (!test) return ''
  const kind = test.settings.timing.kind.toLowerCase().replace('_', ' ')
  return `${test.totals.questions} Qs · ${test.totals.marks} marks · ${kind} ${formatDuration(test.totals.duration_s ?? 0)}`
})

onMounted(() => tests.refresh())
</script>

<template>
  <div class="max-w-2xl space-y-4">
    <UFormField label="Test" :hint="facts">
      <USelectMenu
        v-model="testId"
        :items="items"
        value-key="value"
        :loading="tests.pending.value"
        placeholder="Choose a test"
        class="w-full"
      >
        <template #item-trailing="{ item }">
          <span v-if="item.suffix" class="text-xs text-error">{{ item.suffix }}</span>
        </template>
      </USelectMenu>
    </UFormField>
    <UAlert
      v-if="tests.error.value"
      color="error"
      variant="subtle"
      :title="problemMessage(tests.error.value)"
      :actions="[{ label: 'Try again', onClick: () => tests.refresh() }]"
    />
    <UAlert
      v-else-if="tests.data.value && !items.length"
      color="info"
      variant="subtle"
      title="No tests to assign yet."
      description="Write one in the Test Library first."
      :actions="[{ label: 'Open the Test Library', to: '/admin/tests' }]"
    />
    <UFormField label="Name" help="Shown to students">
      <UInput v-model="title" class="w-full" :maxlength="200" />
    </UFormField>
  </div>
</template>
