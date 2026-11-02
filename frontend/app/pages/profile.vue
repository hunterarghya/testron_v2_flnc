<script setup lang="ts">
import ProfileForm from '~/features/auth/components/ProfileForm.vue'

definePageMeta({ layout: 'student' })
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-semibold">Profile</h1>
    <ProfileForm />
  </div>
</template>
