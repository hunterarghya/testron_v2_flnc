<!-- P-02 (c): the password the teacher read out [D-5], with 👁 and the on-screen keyboard
     (screens.md §4.0), and Start: fullscreen first (it needs this click), then the sitting.
     A refusal that changes the gate (waiting, closed) asks the gate to look again. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { startAttempt } from '~/features/my-tests/composables/myTestsApi'
import { startProblemText } from '~/features/my-tests/utils/gate-text'
import OnScreenKeyboard from '~/shared/components/OnScreenKeyboard.vue'
import { useSubmit } from '~/shared/composables/useSubmit'
import { enterFullscreen, exitFullscreen } from '~/shared/utils/fullscreen'

const props = defineProps<{ assignmentId: string, requiresPassword: boolean }>()
const emit = defineEmits<{ refresh: [] }>()

// These mean the gate itself has changed since it was last read
const GATE_CHANGES = new Set(['not_open_yet', 'waiting_for_teacher', 'entry_closed', 'no_attempts_left'])

const password = ref('')
const shown = ref(false)
const keyboard = ref(false)
const starting = useSubmit(startAttempt)
const message = computed(() => (starting.problem.value ? startProblemText(starting.problem.value) : null))
const ready = computed(() => !props.requiresPassword || password.value.length > 0)

async function start(): Promise<void> {
  const fullscreen = enterFullscreen()
  const state = await starting.submit(props.assignmentId, props.requiresPassword ? password.value : null)
  await fullscreen
  if (state) {
    await navigateTo(`/attempts/${state.attempt_id}`)
    return
  }
  await exitFullscreen()
  if (GATE_CHANGES.has(starting.problem.value?.code ?? '')) emit('refresh')
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="start">
    <template v-if="requiresPassword">
      <p class="font-medium">
        Test has started! Enter the password from your teacher.
      </p>
      <UFormField label="Password" :error="message ?? undefined">
        <UInput v-model="password" :type="shown ? 'text' : 'password'" autocomplete="off" class="w-full max-w-xs">
          <template #trailing>
            <UButton
              :icon="shown ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="shown ? 'Hide password' : 'Show password'"
              color="neutral"
              variant="link"
              size="sm"
              @click="shown = !shown"
            />
            <UButton
              icon="i-lucide-keyboard"
              aria-label="On-screen keyboard"
              color="neutral"
              variant="link"
              size="sm"
              data-keyboard-toggle
              @click="keyboard = !keyboard"
            />
          </template>
        </UInput>
      </UFormField>
      <OnScreenKeyboard v-model="password" v-model:open="keyboard" />
    </template>
    <UAlert v-else-if="message" color="error" variant="subtle" :title="message" />
    <UButton
      type="submit"
      size="xl"
      icon="i-lucide-maximize"
      label="Start test (fullscreen)"
      :loading="starting.pending.value"
      :disabled="!ready"
    />
  </form>
</template>
