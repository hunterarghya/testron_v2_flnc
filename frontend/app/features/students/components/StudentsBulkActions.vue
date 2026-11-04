<!-- The bulk bar of one T-14 tab: what can be done to the ticked students there. Decline and
     deactivate ask first; deleting asks for the student's name to be typed; Share performance
     opens D-06. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { BulkResult, Group, ListedStatus, StudentRow } from '~/api/types'
import ShareDialog from '~/features/students/components/ShareDialog.vue'
import { bulkSummary, type StudentAction } from '~/features/students/utils/bulk-summary'
import type { ShareChange } from '~/features/students/utils/share-plan'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'

type Confirmable = 'decline' | 'deactivate' | 'delete'

const props = defineProps<{
  tab: ListedStatus
  selected: StudentRow[]
  act: (action: StudentAction, ids: string[]) => Promise<BulkResult>
  anonymize: (id: string, confirmName: string) => Promise<void>
  sharePerformance: (change: ShareChange) => Promise<string>
  groups: Group[]
}>()
const emit = defineEmits<{ done: [] }>()

const toast = useToast()
const confirming = ref<Confirmable | null>(null)
const pending = ref(false)
const sharing = ref(false)
const only = computed(() => (props.selected.length === 1 ? props.selected[0] : undefined))
const people = computed(() => `${props.selected.length} student${props.selected.length === 1 ? '' : 's'}`)
const dialogOpen = computed({
  get: () => confirming.value !== null,
  set: (open: boolean) => { if (!open) confirming.value = null },
})
const dialog = computed(() => {
  switch (confirming.value) {
    case 'decline':
      return { title: `Decline ${people.value}?`, description: 'Declined students can\'t ask to join again.', confirm: 'Decline' }
    case 'deactivate':
      return { title: `Deactivate ${people.value}?`, description: 'They lose access at once. Their history is kept, and you can reactivate them later.', confirm: 'Deactivate' }
    default:
      return { title: `Delete ${only.value?.name}?`, description: 'Their name and email are removed for good. Their results stay in gradebooks as "Deleted student".', confirm: 'Delete permanently' }
  }
})

async function onConfirm(typed: string): Promise<void> {
  if (confirming.value === 'delete') {
    await deleteStudent(typed)
  }
  else if (confirming.value) {
    await run(confirming.value)
  }
}

async function run(action: StudentAction): Promise<void> {
  await guarded(async () => {
    const result = await props.act(action, props.selected.map(student => student.id))
    toast.add({ title: bulkSummary(result, action), color: 'success' })
  })
}

async function share(change: ShareChange): Promise<void> {
  await guarded(async () => {
    toast.add({ title: await props.sharePerformance(change), color: 'success' })
    sharing.value = false
  })
}

async function deleteStudent(typed: string): Promise<void> {
  const student = only.value
  if (student) {
    await guarded(async () => {
      await props.anonymize(student.id, typed)
      toast.add({ title: `${student.name} was deleted`, color: 'success' })
    })
  }
}

async function guarded(work: () => Promise<void>): Promise<void> {
  pending.value = true
  try {
    await work()
    emit('done')
  }
  catch (caught) {
    toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
  }
  finally {
    pending.value = false
    confirming.value = null
  }
}
</script>

<template>
  <template v-if="tab === 'PENDING'">
    <UButton label="Approve" icon="i-lucide-check" :loading="pending" @click="run('approve')" />
    <UButton label="Decline" icon="i-lucide-x" color="error" variant="outline" @click="confirming = 'decline'" />
  </template>
  <template v-else-if="tab === 'ACTIVE'">
    <UButton label="Share performance" icon="i-lucide-chart-column" color="neutral" variant="outline" @click="sharing = true" />
    <UButton label="Deactivate" color="error" variant="outline" @click="confirming = 'deactivate'" />
  </template>
  <template v-else-if="tab === 'DEACTIVATED'">
    <UButton label="Reactivate" :loading="pending" @click="run('reactivate')" />
    <UButton v-if="only" label="Delete permanently" color="error" variant="outline" @click="confirming = 'delete'" />
  </template>

  <ShareDialog v-model:open="sharing" :students="selected" :groups="groups" :pending="pending" @save="share" />
  <ConfirmDialog
    v-model:open="dialogOpen"
    :title="dialog.title"
    :description="dialog.description"
    :confirm-label="dialog.confirm"
    danger
    :pending="pending"
    :typed-confirmation="confirming === 'delete' ? only?.name : undefined"
    @confirm="onConfirm"
  />
</template>
