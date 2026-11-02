<!-- The teacher area: left menu + page panels (frontend_spec.md §1). Pages use UDashboardPanel. -->
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import { navigateTo } from '#imports'
import { useSession } from '~/shared/composables/useSession'

const session = useSession()

// Menu entries are added as their screens are built
const menu: NavigationMenuItem[] = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/admin', exact: true },
  { label: 'Students', icon: 'i-lucide-users', to: '/admin/students' },
]

async function logOut(): Promise<void> {
  await session.logOut()
  await navigateTo('/login')
}
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible>
      <template #header>
        <span class="font-semibold">Teacher</span>
      </template>
      <UNavigationMenu :items="menu" orientation="vertical" />
      <template #footer>
        <UButton :label="session.user.value?.name ?? 'Log out'" icon="i-lucide-log-out" color="neutral" variant="ghost" block @click="logOut" />
      </template>
    </UDashboardSidebar>
    <slot />
  </UDashboardGroup>
</template>
