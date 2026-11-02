import { describe, expect, it } from 'vitest'
import {
  initialKeyboardState,
  type KeyboardState,
  MAX_TYPED_LENGTH,
  pressKey,
} from '~/engine/keyboards'

function typeAll(state: KeyboardState, chars: string): KeyboardState {
  return [...chars].reduce((current, char) => pressKey(current, { kind: 'char', char }), state)
}

describe('on-screen QWERTY keyboard', () => {
  it('starts empty, lower case, on letters', () => {
    expect(initialKeyboardState()).toEqual({ value: '', shift: false, layer: 'letters' })
    expect(initialKeyboardState('ab').value).toBe('ab')
  })

  it('types characters in order', () => {
    expect(typeAll(initialKeyboardState(), 'rina@x.in').value).toBe('rina@x.in')
  })

  it('shift makes only the next letter upper case', () => {
    const shifted = pressKey(initialKeyboardState(), { kind: 'shift' })

    const typed = typeAll(shifted, 'ab')

    expect(typed.value).toBe('Ab')
    expect(typed.shift).toBe(false)
  })

  it('shift pressed twice is off again', () => {
    const state = pressKey(pressKey(initialKeyboardState(), { kind: 'shift' }), { kind: 'shift' })

    expect(state.shift).toBe(false)
  })

  it('backspace removes the last character, and nothing when empty', () => {
    expect(pressKey(initialKeyboardState('abc'), { kind: 'backspace' }).value).toBe('ab')
    expect(pressKey(initialKeyboardState(), { kind: 'backspace' }).value).toBe('')
  })

  it('switches between letters and symbols, dropping shift', () => {
    const shifted = pressKey(initialKeyboardState(), { kind: 'shift' })

    const symbols = pressKey(shifted, { kind: 'layer' })
    const letters = pressKey(symbols, { kind: 'layer' })

    expect(symbols).toMatchObject({ layer: 'symbols', shift: false })
    expect(letters.layer).toBe('letters')
  })

  it('stops at the maximum length', () => {
    const full = initialKeyboardState('x'.repeat(MAX_TYPED_LENGTH))

    expect(pressKey(full, { kind: 'char', char: 'y' })).toBe(full)
  })
})
