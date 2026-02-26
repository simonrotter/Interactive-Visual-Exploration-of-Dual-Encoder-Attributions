<template>
  <div
    class="bg-neutral-100 dark:bg-[rgb(49,49,49)] fixed p-2.5 z-[1000] w-full top-0 flex items-center"
  >
    <p class="ml-10 pt-1 pb-1 pl-2 pr-2 rounded-lg font-bold">Overview</p>
    <p
      @click="router.push({ name: 'image', params: { id: 0 } })"
      class="ml-4 bg-neutral-200 dark:bg-neutral-700 pt-1 pb-1 pl-2 pr-2 rounded-lg cursor-pointer font-bold"
    >
      Images
    </p>
  </div>

  <div style="display: flex; flex-direction: column; height: 100vh">
    <div style="width: 100%; height: 80px"></div>
    <h1 style="text-align: center">Click on a datapoint to show its attribution visualization</h1>
    <div
      style="
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-grow: inherit;
      "
    >
      <LengthStats
        @pointClicked="(index) => router.push({ name: 'detail', params: { id: index } })"
      />
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import LengthStats from '@/components/LengthStats.vue'

const router = useRouter()
</script>
