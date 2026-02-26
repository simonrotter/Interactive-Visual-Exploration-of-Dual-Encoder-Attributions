<template>
  <div class="progress-bar-container" ref="containerRef">
    <div
      class="progress-bar-fill"
      :class="{ 'no-transition': !transitionEnabled }"
      :style="{
        width: percent + '%',
        borderRadius: fillRadius,
        backgroundColor: color,
      }"
    ></div>
    <div class="progress-text absolute inset-x-0 top-1/2 -translate-y-1/2">
      <span v-if="customText.length > 0">{{ customText }}</span>
      <span v-if="!hidePercentage">{{ percent.toFixed(1) }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  value: {
    type: Number,
  },
  hidePercentage: {
    type: Boolean,
    default: false,
  },
  customText: {
    type: String,
    default: '',
  },
  transitionEnabled: {
    type: Boolean,
    default: true,
  },
  color: {
    type: String,
    default: '#19b373a6',
  },
})

const percent = computed(() => Math.max(0, Math.min(1, props.value)) * 100)

const containerRef = ref<HTMLElement | null>(null)
const containerWidth = ref(0)

let observer: ResizeObserver | null = null

onMounted(() => {
  if (containerRef.value) {
    observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          containerWidth.value = entry.contentRect.width
        }
      }
    })
    observer.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  if (observer && containerRef.value) {
    observer.unobserve(containerRef.value)
  }
})

//Compute dynamic border-radius based on width between 5 and 33 px bwidth the radius changes from 11 to 0. this is for normal progress bar just little eyecandy but for the doubleslider its essential
const fillRadius = computed(() => {
  const fullRadius = 11
  const minRadius = 0
  const minRadiusWidth = 5
  const noRadiusWidth = 33

  const fillWidthPx = (percent.value / 100) * containerWidth.value

  if (fillWidthPx >= noRadiusWidth) {
    return `${fullRadius}px`
  } else if (fillWidthPx <= minRadiusWidth) {
    return `${minRadius}px`
  } else {
    const ratio = (fillWidthPx - minRadiusWidth) / (noRadiusWidth - minRadiusWidth)
    const interpolatedRadius = fullRadius * ratio
    return `${interpolatedRadius}px`
  }
})
</script>

<style scoped>
.progress-bar-container {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #41414170;
  backdrop-filter: blur(20px);
  border-radius: 11px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  transition:
    width 0.3s ease,
    border-radius 0.3s ease;
}

.no-transition {
  transition: none !important;
}
.progress-text {
  width: 100%;
  text-align: center;
  font-size: 14px;
  color: #ffffff;
  font-weight: semibold;
  text-shadow: 0 0 6px rgba(0, 0, 0, 0.921);
  user-select: none;
}
.progress-text span {
  margin-left: 3px;
  margin-right: 3px;
}
</style>
