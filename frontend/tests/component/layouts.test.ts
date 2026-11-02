import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'
import ExamLayout from '~/layouts/exam.vue'
import PublicLayout from '~/layouts/public.vue'
import StudentLayout from '~/layouts/student.vue'
import TeacherLayout from '~/layouts/teacher.vue'

const page = defineComponent({ render: () => h('p', 'page content') })

describe('layouts', () => {
  it.each([
    ['public', PublicLayout],
    ['student', StudentLayout],
    ['teacher', TeacherLayout],
    ['exam', ExamLayout],
  ])('%s layout shows the page inside it', async (_name, layout) => {
    const wrapper = await mountSuspended(layout, { slots: { default: () => h(page) } })

    expect(wrapper.text()).toContain('page content')
  })

  it('teacher layout links to the dashboard', async () => {
    const wrapper = await mountSuspended(TeacherLayout)

    expect(wrapper.find('a[href="/admin"]').exists()).toBe(true)
  })

  it('exam layout has no links to click away to', async () => {
    const wrapper = await mountSuspended(ExamLayout, { slots: { default: () => h(page) } })

    expect(wrapper.findAll('a')).toHaveLength(0)
  })
})
