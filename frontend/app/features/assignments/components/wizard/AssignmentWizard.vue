<!-- T-07 New Assignment: four steps, each can be revisited. Create freezes the paper and
     opens the overview (T-08). `fromId` starts from an earlier assignment ("Assign again"). -->
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { navigateTo } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import GateFields from '~/features/assignments/components/when/GateFields.vue'
import ResultsFields from '~/features/assignments/components/when/ResultsFields.vue'
import TimingFields from '~/features/assignments/components/when/TimingFields.vue'
import WindowFields from '~/features/assignments/components/when/WindowFields.vue'
import WizardReview from '~/features/assignments/components/wizard/WizardReview.vue'
import WizardStudentsStep from '~/features/assignments/components/wizard/WizardStudentsStep.vue'
import WizardTestStep from '~/features/assignments/components/wizard/WizardTestStep.vue'
import { STEPS, useAssignmentWizard } from '~/features/assignments/composables/useAssignmentWizard'
import { fieldErrors } from '~/shared/utils/form-errors'

const props = defineProps<{ fromId?: string, testId?: string }>()

const wizard = useAssignmentWizard()
const { step, test, title, groupIds, audience, form, timing, creating, canContinue } = wizard
const items = STEPS.map(label => ({ title: label }))
const errors = computed(() => fieldErrors(creating.problem.value))

async function create(): Promise<void> {
  const created = await wizard.create()
  if (created) await navigateTo(`/admin/assignments/${created.id}`)
}

onMounted(async () => {
  if (props.fromId) await wizard.startFrom(props.fromId)
  else if (props.testId) await wizard.pickTest(props.testId)
})
</script>

<template>
  <div class="space-y-6">
    <UStepper v-model="step" :items="items" linear class="max-w-3xl" />
    <WizardTestStep v-if="step === 0" v-model:title="title" :test="test" @pick="wizard.pickTest" />
    <WizardStudentsStep
      v-else-if="step === 1"
      v-model:audience="audience"
      :group-ids="groupIds"
      @pick-groups="wizard.pickGroups"
      @add="wizard.addStudents"
    />
    <div v-else-if="step === 2 && form && test" class="max-w-3xl space-y-8">
      <WindowFields v-model="form" :errors="errors" />
      <GateFields v-model="form" :errors="errors" />
      <section v-if="timing.edit" class="space-y-2">
        <h3 class="text-sm font-medium">
          Timing (from test)
        </h3>
        <TimingFields v-model:edit="timing.edit" v-model:changed="timing.changed" :test="test" :error="errors['timing_override.kind']" />
      </section>
      <ResultsFields v-model="form" :errors="errors" />
    </div>
    <WizardReview v-else-if="step === 3 && form" :title="title" :audience="audience" :form="form" />

    <UAlert
      v-if="creating.problem.value"
      color="error"
      variant="subtle"
      :title="problemMessage(creating.problem.value)"
      :description="Object.values(errors).join(' ')"
    />
    <div class="flex gap-2">
      <UButton v-if="step > 0" label="Back" color="neutral" variant="outline" @click="step--" />
      <UButton v-if="step < STEPS.length - 1" label="Continue" :disabled="!canContinue" @click="step++" />
      <UButton v-else label="Create" icon="i-lucide-check" :loading="creating.pending.value" @click="create" />
    </div>
  </div>
</template>
