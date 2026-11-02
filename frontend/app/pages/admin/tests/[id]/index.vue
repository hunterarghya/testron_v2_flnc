<script setup lang="ts">
import { useRoute } from '#imports'
import TestEditor from '~/features/editor/components/TestEditor.vue'

definePageMeta({ layout: 'teacher' })
const route = useRoute()
</script>

<template>
  <UDashboardPanel id="test-editor">
    <template #header>
      <UDashboardNavbar title="Test" />
    </template>
    <template #body>
      <TestEditor :key="String(route.params.id)" :test-id="String(route.params.id)" />
    </template>
  </UDashboardPanel>
</template>
