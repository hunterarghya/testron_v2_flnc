<!-- The student area: a top bar and comfortable content (frontend_spec.md §1, screens.md
     Student shell). Performance joins the menu in Phase 7. -->
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const menu: NavigationMenuItem[] = [
  { label: 'My Tests', icon: 'i-lucide-clipboard-list', to: '/', exact: true },
  { label: 'Past Tests', icon: 'i-lucide-history', to: '/past' },
  { label: 'Profile', icon: 'i-lucide-user', to: '/profile' },
]
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
