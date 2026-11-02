<!-- P-11 Profile: change the name, change (or, for Google-only accounts, set) the password,
     log out. The email is shown but can't be changed here. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { navigateTo, useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { changePassword, updateName } from '~/features/auth/composables/authApi'
import { useSession } from '~/shared/composables/useSession'
import { useSubmit } from '~/shared/composables/useSubmit'

const session = useSession()
const toast = useToast()
const user = computed(() => session.user.value)
const name = ref(user.value?.name ?? '')
const currentPassword = ref('')
const newPassword = ref('')
const renaming = useSubmit(updateName)
const changing = useSubmit(changePassword)
const hasPassword = computed(() => user.value?.has_password ?? true)

async function onRename(): Promise<void> {
  const updated = await renaming.submit(name.value)
  if (updated) {
    session.set(updated)
    name.value = updated.name
    toast.add({ title: 'Name saved', color: 'success' })
  }
}

async function onChangePassword(): Promise<void> {
  await changing.submit(hasPassword.value ? currentPassword.value : null, newPassword.value)
  if (!changing.problem.value) {
    currentPassword.value = ''
    newPassword.value = ''
    await session.load()
    toast.add({ title: 'Password changed', description: 'Other devices were logged out.', color: 'success' })
  }
}

async function logOut(): Promise<void> {
  await session.logOut()
  await navigateTo('/login')
}
</script>

<template>
  <div class="max-w-xl space-y-6">
    <UCard>
      <form class="space-y-4" @submit.prevent="onRename">
        <UFormField label="Name" :error="renaming.problem.value ? problemMessage(renaming.problem.value) : undefined">
          <div class="flex gap-2">
            <UInput v-model="name" class="flex-1" required />
            <UButton type="submit" label="Save" :loading="renaming.pending.value" />
          </div>
        </UFormField>
        <UFormField label="Email">
          <p class="text-muted">{{ user?.email }}</p>
        </UFormField>
      </form>
    </UCard>
    <UCard>
      <form class="space-y-4" @submit.prevent="onChangePassword">
        <h2 class="font-semibold">{{ hasPassword ? 'Change password' : 'Set a password' }}</h2>
        <UAlert v-if="changing.problem.value" color="error" variant="subtle" :title="problemMessage(changing.problem.value)" />
        <UFormField v-if="hasPassword" label="Current password">
          <UInput v-model="currentPassword" type="password" autocomplete="current-password" class="w-full" required />
        </UFormField>
        <UFormField label="New password" help="8+ characters">
          <UInput v-model="newPassword" type="password" autocomplete="new-password" class="w-full" required />
        </UFormField>
        <UButton type="submit" :label="hasPassword ? 'Change password' : 'Set password'" :loading="changing.pending.value" />
      </form>
    </UCard>
    <UButton label="Log out" color="neutral" variant="outline" icon="i-lucide-log-out" @click="logOut" />
  </div>
</template>
