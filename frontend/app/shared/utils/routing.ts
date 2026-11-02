// Where each kind of account may go (frontend_spec.md §1, screens.md S-01). Pure, so every
// rule is unit-tested; the global route middleware only applies the answer.
import type { SessionUser } from '~/api/types'

const PUBLIC_PATHS = ['/login', '/signup', '/verify-email', '/reset-password']
// Pages a logged-in person is sent away from, to their home
const GUEST_ONLY_PATHS = ['/login', '/signup']
const STATUS_PATH = '/status'

/** The home page for an account: the teacher's dashboard, My Tests, or the status screen. */
export function homeFor(user: SessionUser): string {
  if (user.role === 'TEACHER') {
    return '/admin'
  }
  return user.status === 'ACTIVE' ? '/' : STATUS_PATH
}

/** Where to send someone opening `path` instead, or null when they may stay. */
export function redirectFor(user: SessionUser | null, path: string, fullPath: string): string | null {
  if (PUBLIC_PATHS.includes(path)) {
    return user && GUEST_ONLY_PATHS.includes(path) ? homeFor(user) : null
  }
  if (!user) {
    return `/login?next=${encodeURIComponent(fullPath)}`
  }
  const home = homeFor(user)
  if (path === STATUS_PATH || home === STATUS_PATH) {
    return path === home ? null : home
  }
  return isTeacherPath(path) === (user.role === 'TEACHER') ? null : home
}

/** A `?next=` value that is safe to follow: a path on this site, never another site. */
export function safeNext(next: unknown): string | null {
  if (typeof next !== 'string' || !next.startsWith('/') || next.startsWith('//')) {
    return null
  }
  return next.includes('\\') ? null : next
}

function isTeacherPath(path: string): boolean {
  return path === '/admin' || path.startsWith('/admin/')
}
