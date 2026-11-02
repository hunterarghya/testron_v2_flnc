<!-- Rich content, read-only (editor_content_spec.md §6): the exam hall, preview, results, answer
     sheets and exports all show content through this one component. Empty content shows nothing. -->
<script setup lang="ts">
import 'katex/dist/katex.min.css'
import { computed, defineComponent } from 'vue'
import type { RichDoc } from '~/api/types'
import type { PmNode } from '~/shared/components/rich-content/convert'
import { renderNodes } from '~/shared/components/rich-content/render'

const props = defineProps<{
  doc: RichDoc | null | undefined
  // The exam hall's current question loads its images at once (editor_content_spec.md §5.2)
  eagerImages?: boolean
}>()

const blocks = computed(() => (props.doc?.content ?? []) as PmNode[])
const Content = defineComponent({ setup: () => () => renderNodes(blocks.value, props.eagerImages) })

defineExpose({ isEmpty: computed(() => blocks.value.length === 0) })
</script>

<template>
  <div v-if="blocks.length" class="rich-content space-y-2 break-words">
    <Content />
  </div>
</template>
