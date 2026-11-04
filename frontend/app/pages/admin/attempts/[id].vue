<script setup lang="ts">
import { useRoute, useRouter } from '#imports'
import AnswerSheetView from '~/features/assignments/components/results/AnswerSheetView.vue'

definePageMeta({ layout: 'teacher' })

const route = useRoute()
const router = useRouter()
const attemptId = String(route.params.id)
</script>

<template>
  <UDashboardPanel id="answer-sheet">
    <template #header>
      <UDashboardNavbar title="Answer sheet">
        <template #leading>
          <UButton icon="i-lucide-arrow-left" aria-label="Back to the results" variant="ghost" @click="router.back()" />
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <AnswerSheetView :attempt-id="attemptId" />
    </template>
  </UDashboardPanel>
</template>
