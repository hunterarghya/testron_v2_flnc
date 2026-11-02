// What every form needs around one action: pending while it runs, the problem if it failed.
import { type Ref, ref, shallowRef } from 'vue'
import { type ApiProblem, toProblem } from '~/api/problems'

export interface Submit<Args extends unknown[], Result> {
  pending: Ref<boolean>
  problem: Ref<ApiProblem | null>
  /** Runs the action; resolves to its result, or undefined when it failed (see `problem`). */
  submit: (...args: Args) => Promise<Result | undefined>
}

export function useSubmit<Args extends unknown[], Result>(
  action: (...args: Args) => Promise<Result>,
): Submit<Args, Result> {
  const pending = ref(false)
  const problem = shallowRef<ApiProblem | null>(null)

  async function submit(...args: Args): Promise<Result | undefined> {
    pending.value = true
    problem.value = null
    try {
      return await action(...args)
    }
    catch (caught) {
      // API problems become form state; anything else is a bug and is re-thrown
      problem.value = toProblem(caught)
      return undefined
    }
    finally {
      pending.value = false
    }
  }

  return { pending, problem, submit }
}
