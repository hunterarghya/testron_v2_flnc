<!-- S-01 Log in. One message for every failed login; the on-screen keyboard (⌨) can type into
     either field. After login: the page the person came from, or their home. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { navigateTo, useRoute } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { logIn } from '~/features/auth/composables/authApi'
import OnScreenKeyboard from '~/shared/components/OnScreenKeyboard.vue'
import { useSession } from '~/shared/composables/useSession'
import { useSubmit } from '~/shared/composables/useSubmit'
import { homeFor, safeNext } from '~/shared/utils/routing'

type Field = 'email' | 'password'

const route = useRoute()
const session = useSession()
const form = ref<Record<Field, string>>({ email: '', password: '' })
const keyboardFor = ref<Field>('email')
const keyboardOpen = ref(false)
const typedOnKeyboard = computed({
  get: () => form.value[keyboardFor.value],
  set: (value: string) => { form.value[keyboardFor.value] = value },
})
const { pending, problem, submit } = useSubmit(logIn)
const notice = computed(() => (route.query.reset ? 'Password changed. Log in.' : null))

function openKeyboard(field: Field): void {
  keyboardOpen.value = !(keyboardOpen.value && keyboardFor.value === field)
  keyboardFor.value = field
}

async function onSubmit(): Promise<void> {
  keyboardOpen.value = false
  const user = await submit(form.value.email, form.value.password)
  if (user) {
    session.set(user)
    await navigateTo(safeNext(route.query.next) ?? homeFor(user))
  }
  else if (problem.value?.code === 'email_not_verified') {
    await navigateTo({ path: '/verify-email', query: { email: form.value.email } })
  }
}
</script>

<template>
  <UCard>
    <form class="space-y-4" @submit.prevent="onSubmit">
      <h1 class="text-xl font-semibold">Log in</h1>
      <UAlert v-if="notice" color="success" variant="subtle" :title="notice" />
      <UAlert v-if="problem" color="error" variant="subtle" :title="problemMessage(problem)" />
      <UFormField label="Email" name="email">
        <UInput v-model="form.email" type="email" autocomplete="username" class="w-full" required>
          <template #trailing>
            <UButton icon="i-lucide-keyboard" aria-label="On-screen keyboard for email" color="neutral" variant="link" data-keyboard-toggle @click="openKeyboard('email')" />
          </template>
        </UInput>
      </UFormField>
      <UFormField label="Password" name="password">
        <UInput v-model="form.password" type="password" autocomplete="current-password" class="w-full" required>
          <template #trailing>
            <UButton icon="i-lucide-keyboard" aria-label="On-screen keyboard for password" color="neutral" variant="link" data-keyboard-toggle @click="openKeyboard('password')" />
          </template>
        </UInput>
      </UFormField>
      <div class="flex justify-end">
        <ULink to="/reset-password" class="text-sm">Forgot password?</ULink>
      </div>
      <UButton type="submit" label="Log in" block :loading="pending" />
      <p class="text-center text-sm text-muted">
        New student? <ULink to="/signup">Create an account</ULink>
      </p>
    </form>
    <OnScreenKeyboard v-model="typedOnKeyboard" v-model:open="keyboardOpen" />
  </UCard>
</template>
