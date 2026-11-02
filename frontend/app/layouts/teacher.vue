<!-- The teacher area: left menu + page panels (frontend_spec.md §1). Pages use UDashboardPanel. -->
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

// Menu entries are added as their screens are built
const menu: NavigationMenuItem[] = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/admin' },
]
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible>
      <template #header>
        <span class="font-semibold">Teacher</span>
      </template>
      <UNavigationMenu :items="menu" orientation="vertical" />
    </UDashboardSidebar>
    <slot />
  </UDashboardGroup>
</template>
