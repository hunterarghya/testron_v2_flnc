<!-- T-19 Settings: Profile · Defaults · Branding. -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ProfileForm from '~/features/auth/components/ProfileForm.vue'
import BrandingForm from '~/features/settings/components/BrandingForm.vue'
import DefaultsForm from '~/features/settings/components/DefaultsForm.vue'
import { useAppSettings } from '~/features/settings/composables/useAppSettings'
import ErrorState from '~/shared/components/ErrorState.vue'

definePageMeta({ layout: 'teacher' })

const TABS = [
  { value: 'profile', label: 'Profile' },
  { value: 'defaults', label: 'Defaults' },
  { value: 'branding', label: 'Branding' },
]
const tab = ref('profile')
const { settings, save } = useAppSettings()
onMounted(settings.refresh)
</script>

<template>
  <UDashboardPanel id="settings">
    <template #header>
      <UDashboardNavbar title="Settings" />
    </template>
    <template #body>
      <div class="space-y-4">
        <UTabs v-model="tab" :items="TABS" :content="false" />
        <ProfileForm v-if="tab === 'profile'" />
        <ErrorState v-else-if="settings.error.value" :problem="settings.error.value" @retry="settings.refresh" />
        <template v-else-if="settings.data.value">
          <DefaultsForm v-if="tab === 'defaults'" :settings="settings.data.value" :save="save" />
          <BrandingForm v-else :settings="settings.data.value" :save="save" />
        </template>
        <USkeleton v-else class="h-40 w-full max-w-xl" />
      </div>
    </template>
  </UDashboardPanel>
</template>
