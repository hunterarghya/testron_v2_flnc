<script setup lang="ts">
import { useRoute } from '#imports'
import AssignmentOverview from '~/features/assignments/components/overview/AssignmentOverview.vue'

definePageMeta({ layout: 'teacher' })

const route = useRoute()
const assignmentId = String(route.params.id)
</script>

<template>
  <UDashboardPanel id="assignment">
    <template #header>
      <UDashboardNavbar title="Assignment">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" aria-label="Back to assignments" variant="ghost" to="/admin/assignments" />
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <AssignmentOverview :assignment-id="assignmentId" />
    </template>
  </UDashboardPanel>
</template>
