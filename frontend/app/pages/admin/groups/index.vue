<script setup lang="ts">
import GroupsTable from '~/features/groups/components/GroupsTable.vue'

definePageMeta({ layout: 'teacher' })
</script>

<template>
  <UDashboardPanel id="groups">
    <template #header>
      <UDashboardNavbar title="Groups" />
    </template>
    <template #body>
      <GroupsTable />
    </template>
  </UDashboardPanel>
</template>
