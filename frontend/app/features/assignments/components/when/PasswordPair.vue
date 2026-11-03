<!-- New + Confirm password, each with 👁 [D-5, D-07]. 4 to 32 characters; they must match. -->
<script setup lang="ts">
import { computed, ref } from 'vue'

defineProps<{ error?: string }>()
const password = defineModel<string>('password', { required: true })
const confirm = defineModel<string>('confirm', { required: true })

const shown = ref(false)
const mismatch = computed(() => confirm.value !== '' && confirm.value !== password.value)
const confirmError = computed(() => (mismatch.value ? "The two passwords don't match" : undefined))
const type = computed(() => (shown.value ? 'text' : 'password'))
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2">
    <UFormField label="New password" :error="error" help="4 to 32 characters">
      <UInput v-model="password" :type="type" :maxlength="32" autocomplete="new-password">
        <template #trailing>
          <UButton
            :icon="shown ? 'i-lucide-eye-off' : 'i-lucide-eye'"
            :aria-label="shown ? 'Hide password' : 'Show password'"
            color="neutral"
            variant="link"
            size="sm"
            @click="shown = !shown"
          />
        </template>
      </UInput>
    </UFormField>
    <UFormField label="Confirm password" :error="confirmError">
      <UInput v-model="confirm" :type="type" :maxlength="32" autocomplete="new-password" />
    </UFormField>
  </div>
</template>
