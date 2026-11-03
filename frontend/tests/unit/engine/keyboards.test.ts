import { describe, expect, it } from 'vitest'
import {
  applyNumericKey,
  applyNumericText,
  initialKeyboardState,
  isCompleteNumber,
  type KeyboardState,
  MAX_NUMERIC_LENGTH,
  MAX_TYPED_LENGTH,
  NUMERIC_KEYS,
  type NumericKey,
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

describe('numeric keypad', () => {
  const press = (keys: NumericKey[]): string => keys.reduce(applyNumericKey, '')

  it('builds a decimal number', () => {
    expect(press(['-', '1', '2', '.', '5'])).toBe('-12.5')
  })

  it('allows a minus only first and one point', () => {
    expect(press(['1', '-'])).toBe('1')
    expect(press(['1', '.', '2', '.'])).toBe('1.2')
  })

  it('stops at the server limits and at 12 characters', () => {
    expect(press(Array<NumericKey>(9).fill('9'))).toBe('99999999')
    expect(press(['1', '.', ...Array<NumericKey>(7).fill('5')])).toBe('1.555555')
    expect(press(['-', ...Array<NumericKey>(8).fill('1'), '.', '2', '2', '2', '2'])).toBe('-11111111.22')
  })

  it('backspace and clear', () => {
    expect(applyNumericKey('12', 'backspace')).toBe('1')
    expect(applyNumericKey('12', 'clear')).toBe('')
  })

  it('typed text goes through the same rules (E-18)', () => {
    expect(applyNumericText('', '−12.5')).toBe('-12.5')
    expect(applyNumericText('', '4e2')).toBe('42')
    expect(applyNumericText('', '12,5')).toBe('125')
    expect(applyNumericText('', '１')).toBe('')
  })

  it('only a complete number is saved', () => {
    expect(isCompleteNumber('-12.5')).toBe(true)
    expect(isCompleteNumber('-')).toBe(false)
    expect(isCompleteNumber('12.')).toBe(false)
    expect(NUMERIC_KEYS).toHaveLength(12)
    expect(MAX_NUMERIC_LENGTH).toBe(12)
  })
})
