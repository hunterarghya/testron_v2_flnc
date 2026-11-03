<!-- T-07 ③ presets and Window: when students may sit it. Times are Indian time. -->
<script setup lang="ts">
import { computed } from 'vue'
import { type Preset, type WhenForm, type WindowKind, applyPreset, presetOf } from '~/features/assignments/utils/when-form'

defineProps<{ errors: Record<string, string> }>()
const form = defineModel<WhenForm>({ required: true })

const PRESETS: { value: Preset, label: string, icon?: string }[] = [
  { value: 'LOCKED', label: 'Locked', icon: 'i-lucide-lock' },
  { value: 'SCHEDULED', label: 'Scheduled' },
  { value: 'DEADLINE', label: 'Deadline' },
  { value: 'OPEN', label: 'Open' },
]
const KINDS: { value: WindowKind, label: string }[] = [
  { value: 'MANUAL', label: 'Manual: starts when I press Start' },
  { value: 'SCHEDULED', label: 'Scheduled at a time' },
  { value: 'DEADLINE', label: 'Deadline: open from … to …' },
  { value: 'OPEN', label: 'Open: any time' },
]
const preset = computed(() => presetOf(form.value))
const sharedClock = computed(() => form.value.windowKind === 'MANUAL' || form.value.windowKind === 'SCHEDULED')

function update(changes: Partial<WhenForm>): void {
  form.value = { ...form.value, ...changes }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-sm font-medium">Preset</span>
      <UButton
        v-for="item in PRESETS"
        :key="item.value"
        :label="item.label"
        :icon="item.icon"
        :variant="preset === item.value ? 'solid' : 'outline'"
        size="sm"
        @click="form = applyPreset(form, item.value)"
      />
      <UBadge v-if="!preset" label="Custom" color="neutral" variant="subtle" />
    </div>
    <URadioGroup
      :model-value="form.windowKind"
      :items="KINDS"
      legend="Window"
      @update:model-value="kind => update({ windowKind: kind as WindowKind })"
    />
    <div class="grid gap-3 sm:grid-cols-2">
      <UFormField v-if="form.windowKind === 'MANUAL'" label="Planned for (optional)" :error="errors['window.planned_at']">
        <UInput :model-value="form.plannedAt" type="datetime-local" @update:model-value="v => update({ plannedAt: String(v) })" />
      </UFormField>
      <UFormField v-if="form.windowKind === 'SCHEDULED'" label="Starts at" :error="errors['window.starts_at']">
        <UInput :model-value="form.startsAt" type="datetime-local" @update:model-value="v => update({ startsAt: String(v) })" />
      </UFormField>
      <template v-if="form.windowKind === 'DEADLINE'">
        <UFormField label="Opens at" :error="errors['window.opens_at']">
          <UInput :model-value="form.opensAt" type="datetime-local" @update:model-value="v => update({ opensAt: String(v) })" />
        </UFormField>
        <UFormField label="Closes at" :error="errors['window.closes_at']">
          <UInput :model-value="form.closesAt" type="datetime-local" @update:model-value="v => update({ closesAt: String(v) })" />
        </UFormField>
      </template>
      <UFormField v-if="sharedClock" label="Late entry until (minutes after the start)" help="Empty: until the test ends" :error="errors['window.late_entry_s']">
        <UInputNumber
          :model-value="form.lateEntryMin ?? undefined"
          :min="0"
          :max="1440"
          @update:model-value="v => update({ lateEntryMin: v ?? null })"
        />
      </UFormField>
    </div>
  </div>
</template>
