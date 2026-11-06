<!-- S-05 Account status: waiting, declined or deactivated. While waiting, it checks again every
     60 s (api_contract.md §4) and moves on to My Tests once the teacher approves. -->
<script setup lang="ts">
import { computed } from 'vue'
import { navigateTo } from '#imports'
import LogoutButton from '~/shared/components/LogoutButton.vue'
import { usePolling } from '~/shared/composables/usePolling'
import { useSession } from '~/shared/composables/useSession'
import { homeFor } from '~/shared/utils/routing'

const STATUS_CHECK_MS = 60_000
const VARIANTS = {
  PENDING: { icon: 'i-lucide-hourglass', title: 'Waiting for approval', text: 'Your request was sent to your teacher. You\'ll be able to see tests once you\'re approved.' },
  DECLINED: { icon: 'i-lucide-circle-x', title: 'Request declined', text: 'Your teacher declined this request.' },
  DEACTIVATED: { icon: 'i-lucide-ban', title: 'Account deactivated', text: 'Your teacher has deactivated this account.' },
} as const

const session = useSession()
const variant = computed(() => {
  const status = session.user.value?.status
  return status === 'DECLINED' || status === 'DEACTIVATED' ? VARIANTS[status] : VARIANTS.PENDING
})
const waiting = computed(() => session.user.value?.status === 'PENDING')

async function checkAgain(): Promise<void> {
  const user = await session.load()
  if (!user || user.status === 'ACTIVE') {
    await navigateTo(user ? homeFor(user) : '/login')
  }
}

usePolling(async () => {
  if (waiting.value) {
    await checkAgain()
  }
}, STATUS_CHECK_MS)
</script>

<template>
  <UCard>
    <div class="space-y-4 text-center">
      <UIcon :name="variant.icon" class="mx-auto size-10 text-muted" />
      <h1 class="text-xl font-semibold">{{ variant.title }}</h1>
      <p class="text-muted">{{ variant.text }}</p>
      <div class="flex flex-col items-center gap-2">
        <UButton v-if="waiting" label="Check again" @click="checkAgain" />
        <LogoutButton variant="link" />
      </div>
    </div>
  </UCard>
</template>
