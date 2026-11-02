<script setup lang="ts">
import TestLibrary from '~/features/library/components/TestLibrary.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="tests">
    <template #header>
      <UDashboardNavbar title="Tests" />
    </template>
    <template #body>
      <TestLibrary />
    </template>
  </UDashboardPanel>
</template>
