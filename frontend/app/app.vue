<script setup lang="ts">
import SessionExpiredDialog from '~/shared/components/SessionExpiredDialog.vue'
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <SessionExpiredDialog />
  </UApp>
</template>
