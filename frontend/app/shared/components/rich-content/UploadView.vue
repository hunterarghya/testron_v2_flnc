<!-- An image still uploading: the local preview with a spinner, or "Upload failed" with Retry
     and Remove (editor_content_spec.md §5.1). It is never saved. -->
<script setup lang="ts">
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { onBeforeUnmount } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { forget, upload } from '~/shared/components/rich-content/uploads'

const props = defineProps(nodeViewProps)
const toast = useToast()

function retry(): void {
  void upload(props.editor, props.node.attrs.uploadId, problem => toast.add({ title: problemMessage(problem), color: 'error' }))
}

function remove(): void {
  forget(props.node.attrs.uploadId)
  props.deleteNode()
}

onBeforeUnmount(() => URL.revokeObjectURL(props.node.attrs.previewUrl))
</script>

<template>
  <NodeViewWrapper class="my-2 w-1/2" contenteditable="false">
    <div class="relative">
      <img :src="node.attrs.previewUrl" alt="" class="h-auto max-w-full rounded opacity-60">
      <div class="absolute inset-0 flex items-center justify-center gap-2">
        <template v-if="node.attrs.failed">
          <span class="rounded bg-default px-2 text-sm text-error">Upload failed</span>
          <UButton label="Retry" size="xs" @click="retry" />
          <UButton label="Remove" size="xs" color="neutral" variant="outline" @click="remove" />
        </template>
        <UIcon v-else name="i-lucide-loader" class="size-6 animate-spin" aria-label="Uploading" />
      </div>
    </div>
  </NodeViewWrapper>
</template>
