<!-- T-11 Questions: per question, % correct, the wrong option chosen most and its chapters.
     Clicking one opens the key correction (D-05). -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, h } from 'vue'
import { UButton } from '#components'
import type { KeyedPaper, QuestionStat } from '~/api/types'
import { keyedQuestion } from '~/features/assignments/utils/answer-key'
import DataTable from '~/shared/components/DataTable.vue'

const props = defineProps<{ stats: QuestionStat[], keyed: KeyedPaper | null }>()
const emit = defineEmits<{ correct: [stat: QuestionStat] }>()

type Row = QuestionStat & { id: string }
const rows = computed<Row[]>(() => props.stats.map(s => ({ ...s, id: s.question_id })))

function wrongLabel(stat: QuestionStat): string {
  if (!stat.top_wrong_option_id || !props.keyed) return '–'
  const option = keyedQuestion(props.keyed, stat.question_id)?.options.find(o => o.id === stat.top_wrong_option_id)
  return option ? `${option.label} (${stat.top_wrong_count})` : '–'
}

const columns: TableColumn<Row>[] = [
  {
    id: 'q',
    header: 'Q',
    cell: ({ row }) => h(UButton, {
      'label': `Q${row.original.number} ›`,
      'variant': 'link',
      'aria-label': `Correct the answer for Q${row.original.number}`,
      'onClick': () => emit('correct', row.original),
    }),
  },
  { id: 'type', header: 'Type', cell: ({ row }) => row.original.type },
  {
    id: 'correct',
    header: '% correct',
    cell: ({ row }) => (row.original.answered ? `${Math.round((row.original.correct / row.original.answered) * 100)}%` : '–'),
  },
  { id: 'answered', header: 'Answered', cell: ({ row }) => row.original.answered },
  { id: 'wrong', header: 'Most-chosen wrong', cell: ({ row }) => wrongLabel(row.original) },
  { id: 'tags', header: 'Chapter', cell: ({ row }) => row.original.tags.map(t => t.name).join(', ') || '–' },
]
</script>

<template>
  <DataTable :rows="rows" :columns="columns" empty-title="No questions" />
</template>
