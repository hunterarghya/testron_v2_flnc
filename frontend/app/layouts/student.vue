<!-- The student area: a top bar and comfortable content (frontend_spec.md §1) -->
<template>
  <div class="min-h-screen bg-default">
    <UHeader title="Tests" to="/" />
    <UMain>
      <UContainer class="py-6">
        <slot />
      </UContainer>
    </UMain>
  </div>
</template>
