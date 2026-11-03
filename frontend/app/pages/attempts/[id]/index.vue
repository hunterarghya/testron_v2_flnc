<!-- P-03 the exam hall: no menus, nothing to click away to (frontend_spec.md §1) -->
<script setup lang="ts">
import ExamHall from '~/features/exam-hall/components/ExamHall.vue'

definePageMeta({ layout: 'exam' })

const route = useRoute()
const attemptId = String(route.params.id)
</script>

<template>
  <ExamHall :attempt-id="attemptId" />
</template>
