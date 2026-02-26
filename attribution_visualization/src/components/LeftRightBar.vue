<template>
  <div class="progress-bar-container" ref="containerRef">
    <div
      class="progress-bar-fill left"
      :style="{
        width: -1 * Math.min((value * 100) / 2, 0) + '%',
        borderTopLeftRadius: fillRadius,
        borderBottomLeftRadius: fillRadius,
        borderTopRightRadius: 0,
        borderBottomRightRadius: 0,
        left: 'auto',
        right: '50%',
      }"
    ></div>
    <div
      class="progress-bar-fill right"
      :style="{
        width: Math.max((value * 100) / 2, 0) + '%',
        borderTopRightRadius: fillRadius,
        borderBottomRightRadius: fillRadius,
        borderTopLeftRadius: 0,
        borderBottomLeftRadius: 0,
        left: '50%',
        right: 'auto',
      }"
    ></div>

    <div class="progress-text">
      <span v-if="customText.length > 0">{{ customText }}</span>
      <span v-if="!hideSum">{{ displayedNumber.toFixed(2) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
//percentage bar with two directions
const props = defineProps({
  value: {
    type: Number,
    required: true,
  },
  displayValue: {
    type: Number,
    default: null,
  },
  hideSum: {
    type: Boolean,
    default: false,
  },
  customText: {
    type: String,
    default: '',
  },
})

const value = computed(() => Math.max(-1, Math.min(1, props.value)))
const displayedNumber = computed(() =>
  props.displayValue == null ? props.value : props.displayValue,
)

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

//Compute dynamic border-radius based on width between 5 and 33 px bwidth the radius changes from 8 to 0. this is for normal progress bar just little eyecandy but for the doubleslider its essential
const fillRadius = computed(() => {
  const fullRadius = 8
  const minRadius = 0
  const minRadiusWidth = 5
  const noRadiusWidth = 33

  const fillWidthPx = ((Math.abs(value.value) * 100) / 2 / 100) * containerWidth.value

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
  background-color: #68686870;
  backdrop-filter: blur(20px);
  border-radius: 8px;
  overflow: hidden;
}

.progress-bar-fill {
  position: absolute;
  height: 100%;
  transition:
    width 0.3s ease,
    border-radius 0.3s ease;
}

.progress-bar-fill.right {
  background-color: #b31919a6;
}

.progress-bar-fill.left {
  background-color: #3b82f6a6;
}

.progress-text {
  position: absolute;
  top: 0;
  width: 100%;
  text-align: center;
  font-size: 14px;
  color: #ffffff;
  line-height: 24px;
  font-weight: semibold;
  text-shadow: 0 0 5px rgba(0, 0, 0, 0.7);
  user-select: none;
}
.progress-text span {
  margin-left: 3px;
  margin-right: 3px;
}
</style>
