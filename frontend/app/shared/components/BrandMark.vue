<!-- The coaching centre's logo and name (Settings › Branding), wherever the app introduces
     itself: large above the login and sign-up cards, small in the teacher's menu. It reads
     the shared app info, so a change in Settings shows here at once. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useAppInfo } from '~/shared/composables/useAppInfo'

const props = withDefaults(defineProps<{ size?: 'sm' | 'lg', fallback?: string }>(), { size: 'sm', fallback: 'Teacher' })

const { info } = useAppInfo()
const name = computed(() => info.value?.coaching_name || props.fallback)
const logo = computed(() => info.value?.logo_url ?? null)
</script>

<template>
  <div v-if="size === 'lg'" class="flex flex-col items-center gap-3 text-center">
    <img v-if="logo" :src="logo" alt="" class="size-16 rounded-lg object-contain">
    <p class="text-2xl font-semibold text-highlighted">
      {{ name }}
    </p>
  </div>
  <div v-else class="flex min-w-0 items-center gap-2">
    <img v-if="logo" :src="logo" alt="" class="size-7 rounded object-contain">
    <span class="truncate font-semibold">{{ name }}</span>
  </div>
</template>
