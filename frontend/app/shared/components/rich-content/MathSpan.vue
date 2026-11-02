<!-- One equation in read-only content, drawn by KaTeX (renderMath.ts). -->
<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { renderMath } from '~/shared/components/rich-content/renderMath'

const props = defineProps<{ latex: string, display: boolean }>()
const target = ref<HTMLElement | null>(null)

function draw(): void {
  if (target.value) renderMath(target.value, props.latex, props.display)
}

onMounted(draw)
watch(() => [props.latex, props.display], draw)
</script>

<template>
  <div v-if="display" ref="target" class="my-2 overflow-x-auto text-center" role="math" :aria-label="latex" />
  <span v-else ref="target" role="math" :aria-label="latex" />
</template>
