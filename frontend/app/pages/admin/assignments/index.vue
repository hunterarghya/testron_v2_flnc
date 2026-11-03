<script setup lang="ts">
import AssignmentsList from '~/features/assignments/components/AssignmentsList.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="assignments">
    <template #header>
      <UDashboardNavbar title="Assignments">
        <template #right>
          <UButton icon="i-lucide-plus" label="Assign a test" to="/admin/assignments/new" />
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <AssignmentsList />
    </template>
  </UDashboardPanel>
</template>
