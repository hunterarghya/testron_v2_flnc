<script setup lang="ts">
import ResultsInbox from '~/features/results/components/ResultsInbox.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="results">
    <template #header>
      <UDashboardNavbar title="Results" />
    </template>
    <template #body>
      <ResultsInbox />
    </template>
  </UDashboardPanel>
</template>
