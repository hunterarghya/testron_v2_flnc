<!-- The teacher area: left menu with badges + page panels (screens.md, teacher shell).
     Below 1024 px the menu becomes a drawer (UDashboardSidebar does this). -->
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import { computed, onMounted } from 'vue'
import { navigateTo } from '#imports'
import { useAppInfo } from '~/shared/composables/useAppInfo'
import { BADGES_INTERVAL_MS, useBadges } from '~/shared/composables/useBadges'
import { usePolling } from '~/shared/composables/usePolling'
import { useSession } from '~/shared/composables/useSession'

const session = useSession()
const app = useAppInfo()
const { badges, refresh } = useBadges()

// Menu entries are added as their screens are built
const menu = computed<NavigationMenuItem[]>(() => [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/admin', exact: true },
  { label: 'Tests', icon: 'i-lucide-file-text', to: '/admin/tests' },
  { label: 'Assignments', icon: 'i-lucide-clipboard-list', to: '/admin/assignments' },
  { label: 'Results', icon: 'i-lucide-chart-column', to: '/admin/results', badge: badges.value?.results_to_publish || undefined },
  { label: 'Students', icon: 'i-lucide-users', to: '/admin/students', badge: badges.value?.pending_students || undefined },
  { label: 'Groups', icon: 'i-lucide-users-round', to: '/admin/groups' },
  { label: 'Tags', icon: 'i-lucide-tags', to: '/admin/tags' },
])
const footerMenu: NavigationMenuItem[] = [
  { label: 'Settings', icon: 'i-lucide-settings', to: '/admin/settings' },
]

async function logOut(): Promise<void> {
  await session.logOut()
  await navigateTo('/login')
}

// A failed badge or name load only leaves the menu without them
usePolling(() => refresh().catch(() => undefined), BADGES_INTERVAL_MS)
onMounted(() => app.load().catch(() => undefined))
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible>
      <template #header>
        <div class="flex min-w-0 items-center gap-2">
          <img v-if="app.info.value?.logo_url" :src="app.info.value.logo_url" alt="" class="size-7 rounded object-contain">
          <span class="truncate font-semibold">{{ app.info.value?.coaching_name ?? 'Teacher' }}</span>
        </div>
      </template>
      <UNavigationMenu :items="menu" orientation="vertical" />
      <template #footer>
        <div class="w-full space-y-1">
          <UNavigationMenu :items="footerMenu" orientation="vertical" />
          <UButton :label="session.user.value?.name ?? 'Log out'" icon="i-lucide-log-out" color="neutral" variant="ghost" block @click="logOut" />
        </div>
      </template>
    </UDashboardSidebar>
    <slot />
  </UDashboardGroup>
</template>
