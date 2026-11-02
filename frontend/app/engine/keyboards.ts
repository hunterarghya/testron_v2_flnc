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
