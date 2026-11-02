<script setup lang="ts">
import { useRoute } from '#imports'
import GroupDetail from '~/features/groups/components/GroupDetail.vue'

definePageMeta({ layout: 'teacher' })
const route = useRoute()
</script>

<template>
  <UDashboardPanel id="group">
    <template #header>
      <UDashboardNavbar title="Group" />
    </template>
    <template #body>
      <GroupDetail :key="String(route.params.id)" :group-id="String(route.params.id)" />
    </template>
  </UDashboardPanel>
</template>
