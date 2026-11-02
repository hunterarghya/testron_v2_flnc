// A stand-in for RichField in screen tests: a textarea holding one paragraph per line, so the
// tests exercise the editor's wiring, not TipTap (which has its own tests).
import { defineComponent, h, type PropType } from 'vue'
import type { RichDoc } from '~/api/types'
import { textToDoc } from './docs'

const NEWLINE = String.fromCodePoint(10)

function text(doc: RichDoc | null): string {
  const blocks = (doc?.content ?? []) as { content?: { text?: string }[] }[]
  return blocks.map(block => (block.content ?? []).map(inline => inline.text ?? '').join('')).join(NEWLINE)
}

export const RichFieldStub = defineComponent({
  name: 'RichField',
  props: {
    modelValue: { type: Object as PropType<RichDoc | null>, default: null },
    label: { type: String, default: undefined },
    placeholder: { type: String, default: undefined },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'blur', 'command'],
  setup(props, { emit }) {
    return () => h('textarea', {
      'aria-label': props.label ?? props.placeholder,
      'disabled': props.disabled,
      'value': text(props.modelValue),
      'onInput': (event: Event) => emit('update:modelValue', textToDoc((event.target as HTMLTextAreaElement).value)),
      'onBlur': () => emit('blur'),
    })
  },
})
