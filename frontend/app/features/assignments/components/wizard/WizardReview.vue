<!-- T-07 ④ Review: everything the teacher chose, in plain words, before Create. -->
<script setup lang="ts">
import { computed } from 'vue'
import { type AudienceEntry, tickedIds } from '~/features/assignments/utils/audience'
import { reviewLines } from '~/features/assignments/utils/describe'
import { type WhenForm, toPublication } from '~/features/assignments/utils/when-form'

const props = defineProps<{ title: string, audience: AudienceEntry[], form: WhenForm }>()

const lines = computed(() => [
  `${props.title} · ${tickedIds(props.audience).length} students`,
  ...reviewLines(props.form, toPublication(props.form).delay_s ?? null),
])
</script>

<template>
  <UCard class="max-w-3xl">
    <ul class="space-y-1">
      <li v-for="line in lines" :key="line">
        {{ line }}
      </li>
    </ul>
  </UCard>
</template>
