<!-- T-03's header: where you are, and whether your changes are safe. "Changed elsewhere" (another
     tab) stops editing until a reload; "Offline" keeps changes and retries. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { SaveStatus } from '~/features/editor/utils/save-queue'

const props = defineProps<{ testId: string, title: string, status: SaveStatus, assignedBefore: boolean }>()
const emit = defineEmits<{ reload: [], settings: [], import: [] }>()

const STATUS: Record<SaveStatus, { label: string, icon: string, color: 'neutral' | 'success' | 'warning' | 'error' }> = {
  saved: { label: 'Saved', icon: 'i-lucide-check', color: 'success' },
  saving: { label: 'Saving…', icon: 'i-lucide-loader', color: 'neutral' },
  offline: { label: 'Offline, changes kept', icon: 'i-lucide-wifi-off', color: 'warning' },
  conflict: { label: 'Changed elsewhere', icon: 'i-lucide-triangle-alert', color: 'error' },
  failed: { label: 'Couldn\'t save a change', icon: 'i-lucide-circle-alert', color: 'error' },
}
const shown = computed(() => STATUS[props.status])
const crumbs = computed(() => [{ label: 'Tests', to: '/admin/tests' }, { label: props.title || 'Untitled test' }])
</script>

<template>
  <div class="space-y-2">
    <div class="flex flex-wrap items-center gap-3">
      <UBreadcrumb :items="crumbs" class="min-w-0 flex-1" />
      <UBadge :label="shown.label" :icon="shown.icon" :color="shown.color" variant="subtle" role="status" />
      <UButton label="Preview" icon="i-lucide-eye" color="neutral" variant="outline" size="sm" :to="`/admin/tests/${testId}/preview`" />
      <UButton label="Import" icon="i-lucide-import" color="neutral" variant="outline" size="sm" :disabled="status === 'conflict'" @click="emit('import')" />
      <UButton label="Settings" icon="i-lucide-settings" color="neutral" variant="outline" size="sm" @click="emit('settings')" />
    </div>
    <UAlert
      v-if="status === 'conflict'"
      color="error"
      variant="subtle"
      title="This test was changed in another tab."
      description="Reload to see the latest version. Your unsaved changes here are set aside, not sent."
      :actions="[{ label: 'Reload', color: 'error', onClick: () => emit('reload') }]"
    />
    <UAlert
      v-else-if="assignedBefore"
      color="neutral"
      variant="subtle"
      icon="i-lucide-info"
      title="Edits apply to future assignments. Already-assigned versions are unchanged."
    />
  </div>
</template>
