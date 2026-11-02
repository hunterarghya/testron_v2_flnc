// The state every screen needs around one API read: data, error, pending, refresh
// (frontend_spec.md §3). Feature composables wrap it with their own API call.
import { type Ref, ref, shallowRef } from 'vue'
import { type ApiProblem, toProblem } from '~/api/problems'

export interface ApiData<T> {
  data: Ref<T | null>
  error: Ref<ApiProblem | null>
  pending: Ref<boolean>
  refresh: () => Promise<void>
}

export function useApiData<T>(load: () => Promise<T>): ApiData<T> {
  const data = shallowRef<T | null>(null)
  const error = shallowRef<ApiProblem | null>(null)
  const pending = ref(false)

  async function refresh(): Promise<void> {
    pending.value = true
    try {
      data.value = await load()
      error.value = null
    }
    catch (caught) {
      // API problems become screen state; anything else is a bug and is re-thrown
      error.value = toProblem(caught)
    }
    finally {
      pending.value = false
    }
  }

  return { data, error, pending, refresh }
}
