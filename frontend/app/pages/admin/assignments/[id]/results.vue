<script setup lang="ts">
import { useRoute } from '#imports'
import AssignmentResults from '~/features/assignments/components/results/AssignmentResults.vue'
import ExportMenu from '~/features/exports/components/ExportMenu.vue'

definePageMeta({ layout: 'teacher' })

const route = useRoute()
const assignmentId = String(route.params.id)
</script>

<template>
  <UDashboardPanel id="assignment-results">
    <template #header>
      <UDashboardNavbar title="Results">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" aria-label="Back to the assignment" variant="ghost" :to="`/admin/assignments/${assignmentId}`" />
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <AssignmentResults :assignment-id="assignmentId">
        <template #export="{ title, attemptIds }">
          <ExportMenu :assignment-id="assignmentId" :title="title" :attempt-ids="attemptIds" />
        </template>
      </AssignmentResults>
    </template>
  </UDashboardPanel>
</template>
