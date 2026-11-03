<!-- T-07 ③ "Timing (from test) ✎": changes this assignment's paper only. The kind is the
     test's own; changing it belongs in the test editor. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TestDocument } from '~/api/types'
import type { TimingEdit } from '~/features/assignments/utils/timing'
import { formatDuration } from '~/shared/utils/time'

const props = defineProps<{ test: TestDocument, error?: string }>()
const edit = defineModel<TimingEdit>('edit', { required: true })
const changed = defineModel<boolean>('changed', { required: true })

const open = ref(false)
const kind = computed(() => props.test.settings.timing.kind)
const summary = computed(() => `${kind.value.toLowerCase().replace('_', ' ')} · ${formatDuration(props.test.totals.duration_s ?? 0)}`)

function set(changes: Partial<TimingEdit>): void {
  edit.value = { ...edit.value, ...changes }
  changed.value = true
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center gap-2">
      <span class="text-sm">{{ summary }}</span>
      <UBadge v-if="changed" label="Changed for this assignment" color="warning" variant="subtle" />
      <UButton icon="i-lucide-pencil" aria-label="Change the timing" variant="ghost" size="xs" @click="open = !open" />
    </div>
    <div v-if="open" class="flex flex-wrap gap-3">
      <UFormField v-if="kind === 'TOTAL'" label="Duration (minutes)" :error="error">
        <UInputNumber :model-value="edit.totalMin" :min="1" @update:model-value="v => set({ totalMin: v ?? 1 })" />
      </UFormField>
      <UFormField v-if="kind === 'PER_QUESTION'" label="Seconds per question" :error="error">
        <UInputNumber :model-value="edit.questionS" :min="5" @update:model-value="v => set({ questionS: v ?? 5 })" />
      </UFormField>
      <template v-if="kind === 'SECTIONED'">
        <UFormField v-for="section in test.sections" :key="section.id" :label="`${section.title || 'Section'} (minutes)`">
          <UInputNumber
            :model-value="edit.sectionMin[section.id]"
            :min="1"
            @update:model-value="v => set({ sectionMin: { ...edit.sectionMin, [section.id]: v ?? 1 } })"
          />
        </UFormField>
      </template>
    </div>
  </div>
</template>
