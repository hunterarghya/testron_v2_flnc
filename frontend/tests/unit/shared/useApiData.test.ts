import { describe, expect, it } from 'vitest'
import { ApiProblem } from '~/api/problems'
import { useApiData } from '~/shared/composables/useApiData'

describe('useApiData', () => {
  it('starts empty and holds the loaded data', async () => {
    const state = useApiData(async () => ({ count: 3 }))
    expect(state.data.value).toBeNull()

    await state.refresh()

    expect(state.data.value).toEqual({ count: 3 })
    expect(state.error.value).toBeNull()
    expect(state.pending.value).toBe(false)
  })

  it('is pending while loading', async () => {
    let release: () => void = () => {}
    const state = useApiData(() => new Promise<number>((resolve) => {
      release = () => resolve(1)
    }))

    const loading = state.refresh()
    expect(state.pending.value).toBe(true)
    release()
    await loading

    expect(state.pending.value).toBe(false)
  })

  it('turns an API problem into the error state and clears it on success', async () => {
    const problem = new ApiProblem({ status: 503, code: 'database_unavailable', detail: 'x' })
    let fail = true
    const state = useApiData(async () => {
      if (fail) {
        throw problem
      }
      return 'ok'
    })

    await state.refresh()
    expect(state.error.value).toBe(problem)

    fail = false
    await state.refresh()
    expect(state.error.value).toBeNull()
    expect(state.data.value).toBe('ok')
  })

  it('re-throws bugs instead of showing them as API errors', async () => {
    const state = useApiData(async () => {
      throw new TypeError('bug')
    })

    await expect(state.refresh()).rejects.toThrow('bug')
    expect(state.pending.value).toBe(false)
  })
})
