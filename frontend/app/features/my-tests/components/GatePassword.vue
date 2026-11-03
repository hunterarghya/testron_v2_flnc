<!-- P-02 (c): the password the teacher read out [D-5], with 👁 and the on-screen keyboard
     (screens.md §4.0). The button will enter fullscreen and start the attempt. -->
<script setup lang="ts">
import { ref } from 'vue'
import OnScreenKeyboard from '~/shared/components/OnScreenKeyboard.vue'

defineProps<{ requiresPassword: boolean }>()

const password = ref('')
const shown = ref(false)
const keyboard = ref(false)
</script>

<template>
  <div class="space-y-4">
    <template v-if="requiresPassword">
      <p class="font-medium">
        Test has started! Enter the password from your teacher.
      </p>
      <UFormField label="Password">
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
              @click="keyboard = !keyboard"
            />
          </template>
        </UInput>
      </UFormField>
      <OnScreenKeyboard v-model="password" v-model:open="keyboard" />
    </template>
    <!-- Starting an attempt comes with the exam hall (build_phases.md 5a.3) -->
    <UButton size="xl" icon="i-lucide-maximize" label="Start test (fullscreen)" disabled />
    <p class="text-sm text-muted">
      Starting the test arrives with the exam hall in the next phase.
    </p>
  </div>
</template>
