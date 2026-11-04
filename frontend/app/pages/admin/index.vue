<script setup lang="ts">
import TeacherDashboard from '~/features/results/components/TeacherDashboard.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="dashboard">
    <template #header>
      <UDashboardNavbar title="Dashboard" />
    </template>
    <template #body>
      <TeacherDashboard />
    </template>
  </UDashboardPanel>
</template>
