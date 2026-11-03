// The on-screen QWERTY keyboard as a pure reducer (screens.md §4.0, frontend_spec.md §5.6).
// The component only draws keys; what a key press does to the text is decided here.

export type KeyboardLayer = 'letters' | 'symbols'

export interface KeyboardState {
  value: string
  // Upper case for the next letter only
  shift: boolean
  layer: KeyboardLayer
}

export type KeyPress =
  | { kind: 'char', char: string }
  | { kind: 'backspace' }
  | { kind: 'shift' }
  | { kind: 'layer' }

export const DIGIT_ROW = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '@', '.', '_']
export const LETTER_ROWS = [
  ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
  ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
  ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
]
export const SYMBOL_ROWS = [
  ['!', '#', '$', '%', '&', '*', '(', ')', '+', '='],
  ['?', '/', ':', ';', ',', "'", '"', '~', '^'],
  ['[', ']', '{', '}', '<', '>', '|'],
]
// Long enough for any email or password field it is attached to
export const MAX_TYPED_LENGTH = 254

export function initialKeyboardState(value = ''): KeyboardState {
  return { value, shift: false, layer: 'letters' }
}

export function pressKey(state: KeyboardState, key: KeyPress): KeyboardState {
  switch (key.kind) {
    case 'char':
      return typeChar(state, key.char)
    case 'backspace':
      return { ...state, value: state.value.slice(0, -1) }
    case 'shift':
      return { ...state, shift: !state.shift }
    case 'layer':
      return { ...state, layer: state.layer === 'letters' ? 'symbols' : 'letters', shift: false }
  }
}

function typeChar(state: KeyboardState, char: string): KeyboardState {
  if (state.value.length >= MAX_TYPED_LENGTH) {
    return state
  }
  const typed = state.shift ? char.toUpperCase() : char
  return { ...state, value: state.value + typed, shift: false }
}

// The numeric keypad beside a numerical question (screens.md §4.0). The physical keyboard
// goes through the same reducer, so both behave the same.
export type NumericKey = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '.' | '-' | 'backspace' | 'clear'

export const NUMERIC_KEYS: NumericKey[] = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '0', '.', '-']
export const MAX_NUMERIC_LENGTH = 12
// What may be on the way to a valid number: a minus only first, one point, the server's
// digit limits (8 before the point, 6 after)
const PARTIAL_NUMBER = /^-?\d{0,8}(?:\.\d{0,6})?$/
// The server's rule for a saved value (domain_model.md §3.6 #4)
const COMPLETE_NUMBER = /^-?\d{1,8}(?:\.\d{1,6})?$/

export function applyNumericKey(value: string, key: NumericKey): string {
  if (key === 'clear') return ''
  if (key === 'backspace') return value.slice(0, -1)
  const next = value + key
  return next.length <= MAX_NUMERIC_LENGTH && PARTIAL_NUMBER.test(next) ? next : value
}

/** Typed text, key by key; the typographic minus counts as "-", anything else is ignored. */
export function applyNumericText(value: string, typed: string): string {
  let result = value
  for (const char of typed.replaceAll('−', '-')) {
    if (/^[\d.-]$/.test(char)) result = applyNumericKey(result, char as NumericKey)
  }
  return result
}

/** Only a complete number is saved; "-" or "12." waits for more keys. */
export function isCompleteNumber(value: string): boolean {
  return COMPLETE_NUMBER.test(value)
}
