<script setup lang="ts">
import StudentsTable from '~/features/students/components/StudentsTable.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="students">
    <template #header>
      <UDashboardNavbar title="Students" />
    </template>
    <template #body>
      <StudentsTable />
    </template>
  </UDashboardPanel>
</template>
