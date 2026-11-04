<!-- The body of an exported answer key [H-5]: the paper with each correct answer and its
     solution, through the same question card as results. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { KeyedPaper } from '~/api/types'
import { keyAsQuestions } from '~/features/exports/utils/key-questions'
import ResultQuestionCard from '~/shared/components/result/ResultQuestionCard.vue'

const props = defineProps<{ keyed: KeyedPaper, title: string }>()
const questions = computed(() => keyAsQuestions(props.keyed))
</script>

<template>
  <article class="space-y-4">
    <h1 class="text-xl font-semibold">
      {{ title }} — Answer key
    </h1>
    <ResultQuestionCard v-for="question in questions" :key="question.id" :question="question" printable />
  </article>
</template>
