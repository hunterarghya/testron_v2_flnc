<script setup lang="ts">
import MyResult from '~/features/past-tests/components/MyResult.vue'

definePageMeta({ layout: 'student' })

const route = useRoute()
const attemptId = String(route.params.attemptId)
</script>

<template>
  <MyResult :attempt-id="attemptId" />
</template>
