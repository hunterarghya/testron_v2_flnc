<!-- An image inside the editor (editor_content_spec.md §4.1): select it to resize (S/M/L/Full),
     add a caption or remove it. Never wider than the original. -->
<script setup lang="ts">
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { computed } from 'vue'
import { displayUrl, type ImageSize, SIZE_CLASS } from '~/shared/components/rich-content/image-url'

const props = defineProps(nodeViewProps)

const SIZES: ImageSize[] = ['S', 'M', 'L', 'FULL']
const size = computed(() => (props.node.attrs.size ?? 'M') as ImageSize)
const caption = computed({
  get: () => String(props.node.attrs.caption ?? ''),
  set: (value: string) => props.updateAttributes({ caption: value.slice(0, 300) }),
})
</script>

<template>
  <NodeViewWrapper as="figure" class="my-2 max-w-full space-y-1" :class="SIZE_CLASS[size]">
    <img
      :src="displayUrl(node.attrs.src, size)"
      :alt="node.attrs.alt"
      :width="node.attrs.width"
      :height="node.attrs.height"
      class="h-auto max-w-full rounded"
      :class="{ 'ring-2 ring-primary': selected }"
      draggable="false"
      data-drag-handle
    >
    <figcaption v-if="caption && !selected" class="text-center text-sm text-muted break-words">{{ caption }}</figcaption>
    <div v-if="selected && editor.isEditable" class="flex flex-wrap items-center gap-1" contenteditable="false">
      <UButton
        v-for="option in SIZES"
        :key="option"
        :label="option === 'FULL' ? 'Full' : option"
        size="xs"
        :color="option === size ? 'primary' : 'neutral'"
        :variant="option === size ? 'solid' : 'ghost'"
        @click="updateAttributes({ size: option })"
      />
      <UInput v-model="caption" size="xs" placeholder="Caption" class="flex-1" aria-label="Caption" />
      <UButton icon="i-lucide-trash-2" color="error" variant="ghost" size="xs" aria-label="Remove image" @click="deleteNode" />
    </div>
  </NodeViewWrapper>
</template>
