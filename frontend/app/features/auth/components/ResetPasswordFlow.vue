<!-- S-04 Forgot / reset password. Step 1 always says a code was sent "if an account exists".
     Step 2 needs both the code and the new password (V1 F-01). Every session then ends. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { navigateTo } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { confirmPasswordReset, requestPasswordReset } from '~/features/auth/composables/authApi'
import { useSubmit } from '~/shared/composables/useSubmit'

const step = ref<'email' | 'code'>('email')
const email = ref('')
const digits = ref<string[]>([])
const newPassword = ref('')
const requesting = useSubmit(requestPasswordReset)
const confirming = useSubmit(confirmPasswordReset)
const error = computed(() => {
  const problem = requesting.problem.value ?? confirming.problem.value
  return problem ? problemMessage(problem) : null
})

async function onRequest(): Promise<void> {
  await requesting.submit(email.value)
  if (!requesting.problem.value) {
    step.value = 'code'
  }
}

async function onConfirm(): Promise<void> {
  await confirming.submit(email.value, digits.value.join(''), newPassword.value)
  if (!confirming.problem.value) {
    await navigateTo({ path: '/login', query: { reset: '1' } })
  }
}
</script>

<template>
  <UCard>
    <form v-if="step === 'email'" class="space-y-4" @submit.prevent="onRequest">
      <h1 class="text-xl font-semibold">Reset your password</h1>
      <UAlert v-if="error" color="error" variant="subtle" :title="error" />
      <UFormField label="Email" name="email">
        <UInput v-model="email" type="email" autocomplete="email" class="w-full" required />
      </UFormField>
      <UButton type="submit" label="Send code" block :loading="requesting.pending.value" />
      <p class="text-center text-sm"><ULink to="/login">Back to log in</ULink></p>
    </form>
    <form v-else class="space-y-4" @submit.prevent="onConfirm">
      <h1 class="text-xl font-semibold">Enter code and new password</h1>
      <p class="text-sm text-muted">If an account exists for {{ email }}, we sent it a code.</p>
      <UAlert v-if="error" color="error" variant="subtle" :title="error" />
      <UFormField label="Code">
        <UPinInput v-model="digits" :length="6" otp />
      </UFormField>
      <UFormField label="New password" help="8+ characters">
        <UInput v-model="newPassword" type="password" autocomplete="new-password" class="w-full" required />
      </UFormField>
      <UButton type="submit" label="Set new password" block :loading="confirming.pending.value" :disabled="digits.join('').length < 6" />
    </form>
  </UCard>
</template>
