// Every navigation: load the session once, then send the person where they belong
// (frontend_spec.md §1 "Redirects"). The rules themselves are in shared/utils/routing.ts.
import { defineNuxtRouteMiddleware, navigateTo } from '#imports'
import { useSession } from '~/shared/composables/useSession'
import { redirectFor } from '~/shared/utils/routing'

export default defineNuxtRouteMiddleware(async (to) => {
  const session = useSession()
  if (!session.loaded.value) {
    await session.load()
  }
  const target = redirectFor(session.user.value, to.path, to.fullPath)
  if (target !== null) {
    return navigateTo(target)
  }
})
