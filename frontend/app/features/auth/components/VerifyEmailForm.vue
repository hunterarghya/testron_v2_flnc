<!-- S-03 Verify email. Six boxes that accept a pasted code and submit once full; Resend with a
     visible cooldown. On success the account is Pending and the student sees S-05. -->
<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { navigateTo, useRoute } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { resendCode, verifyEmail } from '~/features/auth/composables/authApi'
import { useSession } from '~/shared/composables/useSession'
import { useSubmit } from '~/shared/composables/useSubmit'
import { homeFor } from '~/shared/utils/routing'

const RESEND_COOLDOWN_S = 60

const route = useRoute()
const session = useSession()
const email = computed(() => String(route.query.email ?? ''))
const masked = computed(() => String(route.query.masked ?? email.value))
const digits = ref<string[]>([])
const verifying = useSubmit(verifyEmail)
const resending = useSubmit(resendCode)
const cooldown = ref(RESEND_COOLDOWN_S)
const timer = setInterval(() => {
  cooldown.value = Math.max(0, cooldown.value - 1)
}, 1000)
onUnmounted(() => clearInterval(timer))

const triesLeft = computed(() => verifying.problem.value?.context.tries_left)
const resendLabel = computed(() => {
  if (cooldown.value === 0) {
    return 'Resend'
  }
  const seconds = String(cooldown.value % 60).padStart(2, '0')
  return `Resend (in ${Math.floor(cooldown.value / 60)}:${seconds})`
})
const error = computed(() => {
  const problem = verifying.problem.value ?? resending.problem.value
  return problem ? problemMessage(problem) : null
})

async function onComplete(): Promise<void> {
  const user = await verifying.submit(email.value, digits.value.join(''))
  if (user) {
    session.set(user)
    await navigateTo(homeFor(user))
  }
}

async function onResend(): Promise<void> {
  await resending.submit(email.value)
  digits.value = []
  cooldown.value = RESEND_COOLDOWN_S
}
</script>

<template>
  <UCard>
    <div class="space-y-4">
      <h1 class="text-xl font-semibold">Check your email</h1>
      <p class="text-muted">We sent a 6-digit code to {{ masked }}</p>
      <UAlert v-if="error" color="error" variant="subtle" :title="error" :description="triesLeft !== undefined ? `${triesLeft} tries left` : undefined" />
      <UPinInput v-model="digits" :length="6" otp autofocus size="xl" :disabled="verifying.pending.value" @complete="onComplete" />
      <UButton label="Verify" block :loading="verifying.pending.value" :disabled="digits.join('').length < 6" @click="onComplete" />
      <p class="text-sm text-muted">
        Didn't get it?
        <UButton
          :label="resendLabel"
          variant="link"
          :disabled="cooldown > 0"
          :loading="resending.pending.value"
          @click="onResend"
        />
      </p>
    </div>
  </UCard>
</template>
