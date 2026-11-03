<script setup lang="ts">
import { useRoute } from '#imports'
import AssignmentMonitor from '~/features/assignments/components/monitor/AssignmentMonitor.vue'

definePageMeta({ layout: 'teacher' })

const route = useRoute()
const assignmentId = String(route.params.id)
</script>

<template>
  <UDashboardPanel id="assignment-monitor">
    <template #header>
      <UDashboardNavbar title="Monitor">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" aria-label="Back to the assignment" variant="ghost" :to="`/admin/assignments/${assignmentId}`" />
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <AssignmentMonitor :assignment-id="assignmentId" />
    </template>
  </UDashboardPanel>
</template>
