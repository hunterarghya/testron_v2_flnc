<!-- Shows that the app reaches the API through the same origin (Phase 0 smoke check) -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useHealth } from '~/features/health/composables/useHealth'
import ErrorState from '~/shared/components/ErrorState.vue'
import { formatDateTime } from '~/shared/utils/time'

const { data, error, pending, refresh } = useHealth()
onMounted(refresh)
</script>

<template>
  <ErrorState v-if="error" :problem="error" @retry="refresh" />
  <USkeleton v-else-if="pending || !data" class="h-6 w-64" />
  <div v-else class="flex items-center gap-2 text-sm">
    <UBadge color="success" variant="subtle" label="Server OK" />
    <span class="text-muted tabular-nums">
      {{ formatDateTime(data.server_now) }} · version {{ data.version }}
    </span>
  </div>
</template>
