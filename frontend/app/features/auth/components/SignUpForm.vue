<!-- S-02 Sign up. Always continues to S-03, whether or not the email was already registered,
     so the form never reveals which emails have accounts. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { navigateTo } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { signUp } from '~/features/auth/composables/authApi'
import { useSubmit } from '~/shared/composables/useSubmit'
import { fieldErrors } from '~/shared/utils/form-errors'

const form = ref({ name: '', email: '', password: '' })
const { pending, problem, submit } = useSubmit(signUp)
const errors = computed(() => fieldErrors(problem.value))
const passwordError = computed(() =>
  problem.value?.code === 'password_too_weak' ? problemMessage(problem.value) : errors.value.password,
)
const generalError = computed(() =>
  problem.value && !Object.keys(errors.value).length && !passwordError.value
    ? problemMessage(problem.value)
    : null,
)

async function onSubmit(): Promise<void> {
  const masked = await submit(form.value.name, form.value.email, form.value.password)
  if (masked !== undefined) {
    await navigateTo({ path: '/verify-email', query: { email: form.value.email.trim(), masked } })
  }
}
</script>

<template>
  <UCard>
    <form class="space-y-4" @submit.prevent="onSubmit">
      <h1 class="text-xl font-semibold">Create your student account</h1>
      <UAlert v-if="generalError" color="error" variant="subtle" :title="generalError" />
      <UFormField label="Full name" name="name" :error="errors.name">
        <UInput v-model="form.name" autocomplete="name" class="w-full" required />
      </UFormField>
      <UFormField label="Email" name="email" :error="errors.email">
        <UInput v-model="form.email" type="email" autocomplete="email" class="w-full" required />
      </UFormField>
      <UFormField label="Password" name="password" help="8+ characters" :error="passwordError">
        <UInput v-model="form.password" type="password" autocomplete="new-password" class="w-full" required />
      </UFormField>
      <UButton type="submit" label="Create account" block :loading="pending" />
      <p class="text-center text-sm text-muted">
        Already have an account? <ULink to="/login">Log in</ULink>
      </p>
    </form>
  </UCard>
</template>
