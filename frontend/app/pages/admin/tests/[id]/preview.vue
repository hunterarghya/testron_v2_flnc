<script setup lang="ts">
import { useRoute } from '#imports'
import TestPreview from '~/features/editor/components/TestPreview.vue'

definePageMeta({ layout: 'teacher' })
const route = useRoute()
</script>

<template>
  <UDashboardPanel id="test-preview">
    <template #header>
      <UDashboardNavbar title="Preview" />
    </template>
    <template #body>
      <TestPreview :key="String(route.params.id)" :test-id="String(route.params.id)" />
    </template>
  </UDashboardPanel>
</template>
