<!-- T-07 ③ Gate: activation, and the password typed twice [D-5]. Editing an assignment
     (T-08) leaves the password to its own dialog, so `withPassword` is off there. -->
<script setup lang="ts">
import type { WhenForm } from '~/features/assignments/utils/when-form'
import PasswordPair from '~/features/assignments/components/when/PasswordPair.vue'

withDefaults(defineProps<{ errors: Record<string, string>, withPassword?: boolean }>(), { withPassword: true })
const form = defineModel<WhenForm>({ required: true })
</script>

<template>
  <div class="space-y-3">
    <UCheckbox
      :model-value="form.requiresActivation || form.windowKind === 'MANUAL'"
      :disabled="form.windowKind === 'MANUAL'"
      label="I must activate it"
      :description="form.windowKind === 'MANUAL' ? 'A manual test always waits for Start.' : undefined"
      @update:model-value="on => form = { ...form, requiresActivation: Boolean(on) }"
    />
    <template v-if="withPassword">
      <UCheckbox
        :model-value="form.usePassword"
        label="Password"
        @update:model-value="on => form = { ...form, usePassword: Boolean(on) }"
      />
      <PasswordPair
        v-if="form.usePassword"
        :password="form.password"
        :confirm="form.passwordConfirm"
        :error="errors.password"
        @update:password="v => form = { ...form, password: v }"
        @update:confirm="v => form = { ...form, passwordConfirm: v }"
      />
    </template>
  </div>
</template>
