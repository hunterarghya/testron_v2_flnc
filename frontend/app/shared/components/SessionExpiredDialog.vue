<!-- "Please log in again" when any request finds the session gone (screens.md §6).
     After login the person returns to the page they were on. -->
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { navigateTo, useRoute } from '#imports'
import { onSessionExpired } from '~/api/session-events'
import { useSession } from '~/shared/composables/useSession'

const open = ref(false)
const route = useRoute()
const session = useSession()
let unsubscribe: (() => void) | undefined

onMounted(() => {
  unsubscribe = onSessionExpired(() => {
    // Someone who was never logged in is simply on a public page
    if (session.user.value !== null) {
      open.value = true
    }
  })
})
onUnmounted(() => unsubscribe?.())

async function logInAgain(): Promise<void> {
  open.value = false
  session.set(null)
  await navigateTo(`/login?next=${encodeURIComponent(route.fullPath)}`)
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Please log in again"
    description="Your session has ended. Log in to carry on where you were."
    :dismissible="false"
    :close="false"
  >
    <template #footer>
      <UButton label="Log in" @click="logInAgain" />
    </template>
  </UModal>
</template>
