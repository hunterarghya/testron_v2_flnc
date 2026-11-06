<!-- "Log out", everywhere it's offered (the teacher's menu, Profile, the account status page):
     it asks first, then ends the session and goes to the login page. -->
<script setup lang="ts">
import type { ButtonProps } from '@nuxt/ui'
import { ref } from 'vue'
import { navigateTo } from '#imports'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import { useSession } from '~/shared/composables/useSession'

defineProps<{
  variant?: ButtonProps['variant']
  block?: boolean
}>()

const session = useSession()
const confirming = ref(false)
const pending = ref(false)

async function logOut(): Promise<void> {
  pending.value = true
  try {
    await session.logOut()
    confirming.value = false
    await navigateTo('/login')
  }
  finally {
    pending.value = false
  }
}
</script>

<!-- Red, like the dialog's confirm button. Full width (the teacher's menu), it is left-aligned like
     the menu items above it. -->
<template>
  <UButton
    label="Log out"
    icon="i-lucide-log-out"
    color="error"
    :variant="variant ?? 'outline'"
    :block="block"
    :class="{ 'justify-start': block }"
    @click="confirming = true"
  />
  <ConfirmDialog
    v-model:open="confirming"
    title="Log out?"
    description="You'll need your email and password to log in again."
    confirm-label="Log out"
    danger
    :pending="pending"
    @confirm="logOut"
  />
</template>
