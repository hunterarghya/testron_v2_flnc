import { describe, expect, it } from 'vitest'
import type { SessionUser } from '~/api/types'
import { homeFor, redirectFor, safeNext } from '~/shared/utils/routing'

function user(role: SessionUser['role'], status: SessionUser['status']): SessionUser {
  return {
    id: 'u1',
    name: 'Someone',
    email: 'someone@example.com',
    role,
    status,
    has_password: true,
    performance_shared: false,
  }
}

const TEACHER = user('TEACHER', null)
const ACTIVE = user('STUDENT', 'ACTIVE')
const PENDING = user('STUDENT', 'PENDING')
const DECLINED = user('STUDENT', 'DECLINED')
const DEACTIVATED = user('STUDENT', 'DEACTIVATED')

describe('homeFor', () => {
  it.each([
    [TEACHER, '/admin'],
    [ACTIVE, '/'],
    [PENDING, '/status'],
    [DECLINED, '/status'],
    [DEACTIVATED, '/status'],
  ])('%o goes home to %s', (who, home) => {
    expect(homeFor(who)).toBe(home)
  })
})

describe('redirectFor (frontend_spec.md §1)', () => {
  it.each([
    // visitors
    [null, '/login', null],
    [null, '/signup', null],
    [null, '/verify-email', null],
    [null, '/reset-password', null],
    [null, '/', '/login?next=%2F'],
    [null, '/admin/students', '/login?next=%2Fadmin%2Fstudents'],
    [null, '/status', '/login?next=%2Fstatus'],
    // logged in on a guest page goes home
    [TEACHER, '/login', '/admin'],
    [ACTIVE, '/signup', '/'],
    [PENDING, '/login', '/status'],
    [ACTIVE, '/reset-password', null],
    // teacher
    [TEACHER, '/admin', null],
    [TEACHER, '/admin/students', null],
    [TEACHER, '/', '/admin'],
    [TEACHER, '/profile', '/admin'],
    [TEACHER, '/status', '/admin'],
    // active student
    [ACTIVE, '/', null],
    [ACTIVE, '/profile', null],
    [ACTIVE, '/admin', '/'],
    [ACTIVE, '/admin/students', '/'],
    [ACTIVE, '/administer', null],
    [ACTIVE, '/status', '/'],
    // waiting, declined and deactivated students only see their status
    [PENDING, '/status', null],
    [PENDING, '/', '/status'],
    [DECLINED, '/admin', '/status'],
    [DEACTIVATED, '/profile', '/status'],
  ] as const)('%o on %s → %s', (who, path, target) => {
    expect(redirectFor(who, path, path)).toBe(target)
  })

  it('keeps the query string in the way back after login', () => {
    expect(redirectFor(null, '/admin/students', '/admin/students?q=rina')).toBe(
      '/login?next=%2Fadmin%2Fstudents%3Fq%3Drina',
    )
  })
})

describe('safeNext (security.md §4.3, open redirects)', () => {
  it.each([
    ['/admin/students', '/admin/students'],
    ['/', '/'],
    ['//evil.example.com', null],
    ['https://evil.example.com', null],
    ['/\\evil.example.com', null],
    ['admin', null],
    [undefined, null],
    [['/a', '/b'], null],
  ])('%o → %o', (next, safe) => {
    expect(safeNext(next)).toBe(safe)
  })
})
