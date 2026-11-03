<script setup lang="ts">
import { useRoute } from '#imports'
import AssignmentLobby from '~/features/assignments/components/lobby/AssignmentLobby.vue'

definePageMeta({ layout: 'teacher' })

const route = useRoute()
const assignmentId = String(route.params.id)
</script>

<template>
  <UDashboardPanel id="assignment-lobby">
    <template #header>
      <UDashboardNavbar title="Lobby">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" aria-label="Back to the assignment" variant="ghost" :to="`/admin/assignments/${assignmentId}`" />
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <AssignmentLobby :assignment-id="assignmentId" />
    </template>
  </UDashboardPanel>
</template>
