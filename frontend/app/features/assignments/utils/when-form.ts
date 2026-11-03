// T-07 step ③ "When & how" as one editable form, its presets [D-2], and the API shapes it
// becomes. Times are datetime-local strings read as Indian time.
import type {
  AssignmentChanges,
  AssignmentDetail,
  AssignmentIntegrity,
  AssignmentWindow,
  Publication,
} from '~/api/types'
import { fromIndianLocal, toIndianLocal } from '~/shared/utils/time'

export type WindowKind = AssignmentWindow['kind']
export type DelayUnit = 'minutes' | 'hours' | 'days'
export type Preset = 'LOCKED' | 'SCHEDULED' | 'DEADLINE' | 'OPEN'

export interface WhenForm {
  windowKind: WindowKind
  plannedAt: string
  startsAt: string
  opensAt: string
  closesAt: string
  lateEntryMin: number | null
  requiresActivation: boolean
  usePassword: boolean
  password: string
  passwordConfirm: string
  integrity: AssignmentIntegrity
  publication: Omit<Publication, 'delay_s'>
  delayValue: number
  delayUnit: DelayUnit
}

const UNIT_S: Record<DelayUnit, number> = { minutes: 60, hours: 3600, days: 86_400 }

// Presets fill in only the window, the gate and the results [D-2]
const PRESETS: Record<Preset, Pick<WhenForm, 'windowKind' | 'requiresActivation' | 'usePassword'> & { mode: Publication['mode'] }> = {
  LOCKED: { windowKind: 'MANUAL', requiresActivation: true, usePassword: true, mode: 'MANUAL' },
  SCHEDULED: { windowKind: 'SCHEDULED', requiresActivation: false, usePassword: false, mode: 'MANUAL' },
  DEADLINE: { windowKind: 'DEADLINE', requiresActivation: false, usePassword: false, mode: 'MANUAL' },
  OPEN: { windowKind: 'OPEN', requiresActivation: false, usePassword: false, mode: 'AUTO_IMMEDIATE' },
}

export function emptyWhenForm(integrity: AssignmentIntegrity): WhenForm {
  return applyPreset({
    windowKind: 'MANUAL',
    plannedAt: '',
    startsAt: '',
    opensAt: '',
    closesAt: '',
    lateEntryMin: null,
    requiresActivation: true,
    usePassword: true,
    password: '',
    passwordConfirm: '',
    integrity: { ...integrity },
    publication: { mode: 'MANUAL', content: 'SCORE_ONLY', show_paper: false, show_solutions: false, show_rank_and_stats: false },
    delayValue: 2,
    delayUnit: 'hours',
  }, 'LOCKED')
}

export function applyPreset(form: WhenForm, preset: Preset): WhenForm {
  const { mode, ...rest } = PRESETS[preset]
  return { ...form, ...rest, publication: { ...form.publication, mode } }
}

/** The preset the form still matches, or null once the teacher changed something ("Custom"). */
export function presetOf(form: WhenForm): Preset | null {
  const found = (Object.keys(PRESETS) as Preset[]).find((name) => {
    const preset = PRESETS[name]
    return preset.windowKind === form.windowKind
      && preset.requiresActivation === form.requiresActivation
      && preset.usePassword === form.usePassword
      && preset.mode === form.publication.mode
  })
  return found ?? null
}

const iso = (local: string) => (local ? fromIndianLocal(local) : undefined)
const lateEntry = (form: WhenForm) => (form.lateEntryMin == null ? undefined : form.lateEntryMin * 60)

export function toWindow(form: WhenForm): AssignmentWindow {
  switch (form.windowKind) {
    case 'MANUAL':
      return { kind: 'MANUAL', planned_at: iso(form.plannedAt), late_entry_s: lateEntry(form) }
    case 'SCHEDULED':
      return { kind: 'SCHEDULED', starts_at: iso(form.startsAt) ?? '', late_entry_s: lateEntry(form) }
    case 'DEADLINE':
      return { kind: 'DEADLINE', opens_at: iso(form.opensAt) ?? '', closes_at: iso(form.closesAt) ?? '' }
    case 'OPEN':
      return { kind: 'OPEN' }
  }
}

export function toPublication(form: WhenForm): Publication {
  const delayed = form.publication.mode === 'AUTO_DELAYED'
  return { ...form.publication, delay_s: delayed ? form.delayValue * UNIT_S[form.delayUnit] : null }
}

/** The form filled from a saved assignment: "Edit settings" (T-08) and "Assign again" (T-06). */
export function whenFormFrom(detail: AssignmentDetail): WhenForm {
  const window = detail.window_summary
  const local = (value?: string | null) => (value ? toIndianLocal(value) : '')
  const { published_at: _published, publish_at: _publishAt, delay_s, ...publication } = detail.publication
  return {
    ...emptyWhenForm(detail.integrity),
    windowKind: detail.window_kind,
    plannedAt: local(window.planned_at),
    startsAt: local(window.starts_at),
    opensAt: local(window.opens_at),
    closesAt: local(window.closes_at),
    lateEntryMin: window.late_entry_s == null ? null : Math.round(window.late_entry_s / 60),
    requiresActivation: detail.gate.requires_activation,
    usePassword: detail.gate.has_password,
    publication,
    ...delayParts(delay_s ?? null),
  }
}

function delayParts(delayS: number | null): Pick<WhenForm, 'delayValue' | 'delayUnit'> {
  if (!delayS) return { delayValue: 2, delayUnit: 'hours' }
  const unit = (['days', 'hours', 'minutes'] as DelayUnit[]).find(name => delayS % UNIT_S[name] === 0) ?? 'minutes'
  return { delayValue: Math.round(delayS / UNIT_S[unit]), delayUnit: unit }
}

/** "Edit settings" (T-08): only the parts the server still accepts (`editable_fields`). */
export function toChanges(form: WhenForm, title: string, editable: string[]): AssignmentChanges {
  const all: AssignmentChanges = {
    title,
    window: toWindow(form),
    gate: { requires_activation: form.requiresActivation },
    integrity: form.integrity,
    publication: toPublication(form),
  }
  return Object.fromEntries(Object.entries(all).filter(([field]) => editable.includes(field)))
}
