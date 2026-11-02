<!-- An equation inside the editor: drawn by KaTeX; click to edit the LaTeX in a popover with a
     live preview (editor_content_spec.md §4.1). A new, empty equation opens straight away. -->
<script setup lang="ts">
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { MATH_BLOCK, MAX_LATEX } from '~/shared/components/rich-content/convert'
import { renderMath } from '~/shared/components/rich-content/renderMath'

const props = defineProps(nodeViewProps)

const display = computed(() => props.node.type.name === MATH_BLOCK)
const latex = computed(() => String(props.node.attrs.latex ?? ''))
const open = ref(false)
const draft = ref('')
const drawn = ref<HTMLElement | null>(null)
const preview = ref<HTMLElement | null>(null)

function draw(target: HTMLElement | null, source: string): void {
  if (target) renderMath(target, source || '\\square', display.value)
}

watch(latex, value => draw(drawn.value, value))
watch(draft, value => draw(preview.value, value))
watch(open, async (isOpen) => {
  if (isOpen) {
    draft.value = latex.value
    // The popover's preview box exists only once it has opened
    await nextTick()
    draw(preview.value, draft.value)
  }
  // Closed with nothing typed: an empty equation means nothing, so it goes
  else if (!latex.value.trim()) {
    props.deleteNode()
  }
})

function done(): void {
  props.updateAttributes({ latex: draft.value.trim() })
  open.value = false
}

onMounted(() => {
  draw(drawn.value, latex.value)
  if (!latex.value && props.editor.isEditable) open.value = true
})
</script>

<template>
  <NodeViewWrapper :as="display ? 'div' : 'span'" :class="display ? 'my-2 text-center' : 'inline-block'">
    <UPopover v-model:open="open" :disabled="!editor.isEditable">
      <span ref="drawn" role="button" tabindex="0" class="cursor-pointer rounded px-0.5 hover:bg-elevated" :class="{ 'ring-2 ring-primary': selected }" :aria-label="`Equation ${latex}`" />
      <template #content>
        <form class="w-80 space-y-2 p-3" @submit.prevent="done">
          <UTextarea v-model="draft" :maxlength="MAX_LATEX" autofocus autoresize placeholder="e.g. \frac{a}{b}" class="w-full font-mono" aria-label="LaTeX" />
          <div ref="preview" class="min-h-8 overflow-x-auto rounded bg-elevated p-2" aria-live="polite" />
          <div class="flex justify-between">
            <UButton label="Remove" color="error" variant="ghost" size="sm" @click="deleteNode" />
            <UButton type="submit" label="Done" size="sm" />
          </div>
        </form>
      </template>
    </UPopover>
  </NodeViewWrapper>
</template>
