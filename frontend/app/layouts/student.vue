<!-- The student area: a top bar and comfortable content (frontend_spec.md §1, screens.md
     Student shell). Performance shows only while the teacher shares it [I-3]. -->
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import { computed } from 'vue'
import { useSession } from '~/shared/composables/useSession'

const { user } = useSession()
const menu = computed<NavigationMenuItem[]>(() => [
  { label: 'My Tests', icon: 'i-lucide-clipboard-list', to: '/', exact: true },
  { label: 'Past Tests', icon: 'i-lucide-history', to: '/past' },
  ...(user.value?.performance_shared ? [{ label: 'Performance', icon: 'i-lucide-chart-column', to: '/performance' }] : []),
  { label: 'Profile', icon: 'i-lucide-user', to: '/profile' },
])
</script>

<template>
  <div class="min-h-screen bg-default">
    <UHeader title="Tests" to="/">
      <UNavigationMenu :items="menu" />
      <template #body>
        <UNavigationMenu :items="menu" orientation="vertical" />
      </template>
    </UHeader>
    <UMain>
      <UContainer class="py-6">
        <slot />
      </UContainer>
    </UMain>
  </div>
</template>
