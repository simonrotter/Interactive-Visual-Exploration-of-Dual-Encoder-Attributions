<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<style>
body {
  @apply bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100;
}
</style>
