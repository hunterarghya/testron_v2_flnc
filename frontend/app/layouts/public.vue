<!-- Login, sign-up, verify, reset, status (screens S-01…S-05): the centre's logo and name above
     one centred card. The branding is read fresh on every visit, so a change shows next time. -->
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useHead } from '#imports'
import BrandMark from '~/shared/components/BrandMark.vue'
import { useAppInfo } from '~/shared/composables/useAppInfo'

const app = useAppInfo()
useHead({ title: computed(() => app.info.value?.coaching_name || 'Test Platform') })

// Without it the card still works; the page just shows no branding
onMounted(() => app.load().catch(() => undefined))
</script>

<template>
  <UMain class="flex min-h-screen items-center justify-center bg-muted p-4">
    <div class="w-full max-w-md space-y-6">
      <BrandMark v-if="app.info.value" size="lg" />
      <slot />
    </div>
  </UMain>
</template>
