<!-- P-04's section bar: one chip per section. Done ones show ✓; the current one its timer;
     ones left but still running (allow return) are clickable with their own timer, which
     keeps running [Q-7]; later ones show their length and are locked. -->
<script setup lang="ts">
import { computed } from 'vue'
import { formatCountdown } from '~/engine/clock'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import { formatDuration } from '~/shared/utils/time'

const props = defineProps<{ nowMs: number, returnable: number[] }>()
const emit = defineEmits<{ return: [index: number] }>()

const hall = useHall()

const chips = computed(() => {
  const state = hall.state.value
  if (!state) return []
  return state.stage_meta.map((meta) => {
    const stage = state.stages[meta.index]
    const name = meta.title ?? `Section ${meta.index + 1}`
    const left = stage?.deadline_at ? Math.max(0, Date.parse(stage.deadline_at) - props.nowMs) : 0
    const current = meta.index === state.current_stage_index
    const canReturn = props.returnable.includes(meta.index)
    return { index: meta.index, label: `S${meta.index + 1} ${name}`, detail: detail(stage?.state, current || canReturn, left, meta.duration_s), current, canReturn }
  })
})

function detail(state: string | undefined, running: boolean, leftMs: number, durationS: number): string {
  if (running) return formatCountdown(leftMs)
  if (state === 'CLOSED') return '✓ done'
  if (state === 'MISSED') return 'missed'
  return formatDuration(durationS)
}
</script>

<template>
  <nav class="flex gap-2 overflow-x-auto border-b border-default px-4 py-2" aria-label="Sections">
    <UButton
      v-for="chip in chips"
      :key="chip.index"
      :label="`${chip.label} · ${chip.detail}`"
      :color="chip.current ? 'primary' : 'neutral'"
      :variant="chip.current ? 'soft' : 'outline'"
      :disabled="!chip.canReturn"
      :aria-current="chip.current ? 'step' : undefined"
      size="sm"
      class="shrink-0"
      @click="emit('return', chip.index)"
    />
  </nav>
</template>
