<script setup lang="ts">
import { useRoute } from '#imports'
import StudentProfile from '~/features/students/components/StudentProfile.vue'

definePageMeta({ layout: 'teacher' })
const route = useRoute()
</script>

<template>
  <UDashboardPanel id="student">
    <template #header>
      <UDashboardNavbar title="Student" />
    </template>
    <template #body>
      <StudentProfile :key="String(route.params.id)" :student-id="String(route.params.id)" />
    </template>
  </UDashboardPanel>
</template>
