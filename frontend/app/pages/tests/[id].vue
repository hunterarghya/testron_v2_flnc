<script setup lang="ts">
import { useRoute } from '#imports'
import TestGate from '~/features/my-tests/components/TestGate.vue'

definePageMeta({ layout: 'student' })

const route = useRoute()
const assignmentId = String(route.params.id)
</script>

<template>
  <TestGate :assignment-id="assignmentId" />
</template>
