<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from '#imports'
import AssignmentWizard from '~/features/assignments/components/wizard/AssignmentWizard.vue'

definePageMeta({ layout: 'teacher' })

// ?from=<assignment> is "Assign again"; ?test=<test> comes from the test library
const route = useRoute()
const fromId = computed(() => (typeof route.query.from === 'string' ? route.query.from : undefined))
const testId = computed(() => (typeof route.query.test === 'string' ? route.query.test : undefined))
</script>

<template>
  <UDashboardPanel id="new-assignment">
    <template #header>
      <UDashboardNavbar title="Assign a test" />
    </template>
    <template #body>
      <AssignmentWizard :from-id="fromId" :test-id="testId" />
    </template>
  </UDashboardPanel>
</template>
