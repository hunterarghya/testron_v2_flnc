<!-- T-08 Password: hidden until 👁 (each reveal is recorded), and Change password with New +
     Confirm (D-07), or remove it. Students never receive it from the server. -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { ApiProblem } from '~/api/problems'
import PasswordPair from '~/features/assignments/components/when/PasswordPair.vue'

const props = defineProps<{
  hasPassword: boolean
  canChange: boolean
  reveal: () => Promise<string | null | undefined>
  save: (password: string | null, confirm?: string) => Promise<unknown>
  pending: boolean
  problem: ApiProblem | null
}>()

const shown = ref<string | null>(null)
const changing = ref(false)
const password = ref('')
const confirm = ref('')

async function toggle(): Promise<void> {
  shown.value = shown.value === null ? ((await props.reveal()) ?? null) : null
}

async function submit(remove: boolean): Promise<void> {
  await props.save(remove ? null : password.value, remove ? undefined : confirm.value)
  if (!props.problem) {
    changing.value = false
    shown.value = null
  }
}

watch(changing, () => {
  password.value = ''
  confirm.value = ''
})
</script>

<template>
  <UCard>
    <template #header>
      <h3 class="font-medium">
        Password
      </h3>
    </template>
    <div class="flex flex-wrap items-center gap-2">
      <template v-if="hasPassword">
        <span class="font-mono">{{ shown ?? '••••••••' }}</span>
        <UButton
          :icon="shown === null ? 'i-lucide-eye' : 'i-lucide-eye-off'"
          :aria-label="shown === null ? 'Reveal password' : 'Hide password'"
          variant="ghost"
          size="xs"
          @click="toggle"
        />
      </template>
      <span v-else class="text-muted">No password</span>
      <UButton
        v-if="canChange"
        class="ms-auto"
        :label="hasPassword ? 'Change password' : 'Set password'"
        size="xs"
        variant="outline"
        @click="changing = true"
      />
    </div>
    <UModal v-model:open="changing" :title="hasPassword ? 'Change password' : 'Set password'" description="Students type it at the gate.">
      <template #body>
        <div class="space-y-3">
          <PasswordPair v-model:password="password" v-model:confirm="confirm" />
          <UAlert v-if="problem" color="error" variant="subtle" :title="problemMessage(problem)" />
        </div>
      </template>
      <template #footer>
        <div class="flex w-full justify-end gap-2">
          <UButton v-if="hasPassword" label="Remove password" color="error" variant="ghost" :loading="pending" @click="submit(true)" />
          <UButton label="Save" :loading="pending" :disabled="!password || password !== confirm" @click="submit(false)" />
        </div>
      </template>
    </UModal>
  </UCard>
</template>
