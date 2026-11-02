<script setup lang="ts">
import TagsTable from '~/features/tags/components/TagsTable.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="tags">
    <template #header>
      <UDashboardNavbar title="Tags" />
    </template>
    <template #body>
      <TagsTable />
    </template>
  </UDashboardPanel>
</template>
