<!-- T-19 Branding: the coaching centre's name and logo, shown in every header and email. The
     logo goes straight from the browser to image storage (api/uploads.ts). -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { AppSettings, AppSettingsChanges } from '~/api/types'
import { IMAGE_TYPES, uploadImage } from '~/api/uploads'
import { useSubmit } from '~/shared/composables/useSubmit'
import { fieldErrors } from '~/shared/utils/form-errors'

const props = defineProps<{
  settings: AppSettings
  save: (changes: AppSettingsChanges) => Promise<AppSettings>
}>()

const toast = useToast()
const name = ref('')
const picker = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const saving = useSubmit(props.save)
const errors = computed(() => fieldErrors(saving.problem.value))
const logo = computed(() => props.settings.logo_url)

watch(() => props.settings.coaching_name, (saved) => {
  name.value = saved
}, { immediate: true })

async function saveName(): Promise<void> {
  if (await saving.submit({ coaching_name: name.value })) {
    toast.add({ title: 'Name saved', color: 'success' })
  }
}

async function onPicked(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) {
    return
  }
  uploading.value = true
  try {
    const uploaded = await uploadImage(file)
    if (await saving.submit({ logo_url: uploaded.url })) {
      toast.add({ title: 'Logo saved', color: 'success' })
    }
  }
  catch (caught) {
    toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
  }
  finally {
    uploading.value = false
  }
}

async function removeLogo(): Promise<void> {
  if (await saving.submit({ logo_url: null })) {
    toast.add({ title: 'Logo removed', color: 'success' })
  }
}
</script>

<template>
  <UCard class="max-w-xl">
    <div class="space-y-6">
      <form class="space-y-2" @submit.prevent="saveName">
        <UFormField label="Coaching centre name" help="Shown in every header and email" :error="errors.coaching_name">
          <div class="flex gap-2">
            <UInput v-model="name" class="flex-1" required />
            <UButton type="submit" label="Save" :loading="saving.pending.value && !uploading" />
          </div>
        </UFormField>
      </form>
      <UFormField label="Logo" help="PNG, JPEG, WebP or GIF, up to 5 MB" :error="errors.logo_url">
        <div class="flex flex-wrap items-center gap-3">
          <img v-if="logo" :src="logo" alt="Current logo" class="size-16 rounded border border-default object-contain">
          <UButton :label="logo ? 'Replace logo' : 'Upload logo'" icon="i-lucide-upload" color="neutral" variant="outline" :loading="uploading" @click="picker?.click()" />
          <UButton v-if="logo" label="Remove" color="error" variant="ghost" @click="removeLogo" />
          <input ref="picker" type="file" :accept="IMAGE_TYPES.join(',')" class="hidden" @change="onPicked">
        </div>
      </UFormField>
    </div>
  </UCard>
</template>
