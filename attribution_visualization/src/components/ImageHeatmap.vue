<template>
  <div class="heatmap-container">
    <div class="image-wrapper" ref="imageWrapper">
      <img
        :src="imageUrl"
        :class="{ grayscale: grayscale }"
        ref="image"
        @load="onImageLoad"
        @mousedown="startBrush"
        @mousemove="updateBrush"
        @mouseup="endBrush"
        draggable="false"
      />
      <!-- heatmap canvas -->
      <canvas ref="heatmapCanvas" class="heatmap-canvas" draggable="false"></canvas>
      <!-- brush overlay canvas -->
      <canvas ref="brushCanvas" class="heatmap-canvas" draggable="false"></canvas>
      <button
        @click="clearBrush"
        class="clear-btn py-1.5 px-3 m-1 bg-neutral-300 dark:bg-neutral-700 border-none rounded cursor-pointer"
      >
        Reset Brush
      </button>
      <!--Buttons to control simulation of changin selections-->
      <!--<button @click="exportDurations">Export timings</button>-->
      <!--<button @click="startSimulation">Start Simulation</button>-->
      <!--<button @click="stopSimulation">Stop Simulation</button>-->
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineEmits, onUnmounted } from 'vue'
const heatmapDurations = ref([])

const props = defineProps({
  imageUrl: String,
  attributions: Array,
  selection: Object,
  viewMode: {
    type: String,
    default: 'Interpolated',
    validator: (value) => ['Dots', 'Interpolated', 'Squares'].includes(value),
  },
  threshold: {
    type: Number,
    default: 0,
  },
  grayscale: {
    type: Boolean,
    default: false,
  },
})

const image = ref(null)
const heatmapCanvas = ref(null)
const brushCanvas = ref(null)
const imageWrapper = ref(null)
const imageLoaded = ref(false)
const brushing = ref(false)
const brushStart = ref(null)
const brushEnd = ref(null)
const showHeatmap = ref(true)

const emit = defineEmits(['brushed-selection'])

const onImageLoad = () => {
  imageLoaded.value = true

  const width = image.value.clientWidth
  const height = image.value.clientHeight

  heatmapCanvas.value.width = width
  heatmapCanvas.value.height = height
  brushCanvas.value.width = width
  brushCanvas.value.height = height

  drawHeatmap()
  clearBrushOverlay()
}

//bilinear interpolation function for 2D array
function bilinearInterpolation(data, H_new, W_new) {
  const H = data.length
  const W = data[0].length
  const result = Array(H_new)
    .fill(0)
    .map(() => Array(W_new).fill(0))

  for (let i = 0; i < H_new; i++) {
    //Corresponding position in original data
    const y = (i * (H - 1)) / (H_new - 1)
    const y0 = Math.floor(y)
    const y1 = Math.min(y0 + 1, H - 1)
    const wy = y - y0

    for (let j = 0; j < W_new; j++) {
      const x = (j * (W - 1)) / (W_new - 1)
      const x0 = Math.floor(x)
      const x1 = Math.min(x0 + 1, W - 1)
      const wx = x - x0

      //bilienar sum of neighbours
      const val =
        data[y0][x0] * (1 - wx) * (1 - wy) +
        data[y0][x1] * wx * (1 - wy) +
        data[y1][x0] * (1 - wx) * wy +
        data[y1][x1] * wx * wy

      result[i][j] = val
    }
  }

  return result
}

function hsvToRgb(h, s, v) {
  let c = v * s
  let x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  let m = v - c
  let r = 0,
    g = 0,
    b = 0

  if (0 <= h && h < 60) [r, g, b] = [c, x, 0]
  else if (60 <= h && h < 120) [r, g, b] = [x, c, 0]
  else if (120 <= h && h < 180) [r, g, b] = [0, c, x]
  else if (180 <= h && h < 240) [r, g, b] = [0, x, c]
  else if (240 <= h && h < 300) [r, g, b] = [x, 0, c]
  else if (300 <= h && h <= 360) [r, g, b] = [c, 0, x]

  return [Math.floor((r + m) * 255), Math.floor((g + m) * 255), Math.floor((b + m) * 255)]
}

const drawHeatmap = () => {
  const start = performance.now()
  const ctx = heatmapCanvas.value?.getContext('2d')

  const hasBrush = brushStart.value && brushEnd.value

  const shouldShowHeatmap =
    image.value &&
    heatmapCanvas.value &&
    props.attributions.length &&
    !showHeatmap.value &&
    !hasBrush

  if (!shouldShowHeatmap) {
    if (ctx && heatmapCanvas.value) {
      ctx.clearRect(0, 0, heatmapCanvas.value.width, heatmapCanvas.value.height)
    }
    const end = performance.now()
    const duration = end - start
    console.log(`Heatmap skipped, took ${duration.toFixed(2)} ms`)
    return
  }

  const H = props.attributions[0].length
  const W = props.attributions[0][0].length

  const selected = props.selection.tokens_a.length
    ? props.selection.tokens_a
    : Array.from({ length: props.attributions.length }, (_, i) => i)

  const heatmap = Array(H)
    .fill(0)
    .map(() => Array(W).fill(0))

  selected.forEach((idx) => {
    const map = props.attributions[idx]
    for (let i = 0; i < H; i++) {
      for (let j = 0; j < W; j++) {
        heatmap[i][j] += map[i][j]
      }
    }
  })

  const H_img = heatmapCanvas.value.height
  const W_img = heatmapCanvas.value.width

  if (props.viewMode === 'Interpolated') {
    const smoothHeatmap = bilinearInterpolation(heatmap, H_img, W_img)

    let maxVal = 0
    for (let i = 0; i < smoothHeatmap.length; i++) {
      for (let j = 0; j < smoothHeatmap[0].length; j++) {
        const absVal = Math.abs(smoothHeatmap[i][j])
        if (absVal > maxVal) maxVal = absVal
      }
    }
    if (maxVal === 0) maxVal = 1

    const imageData = ctx.createImageData(W_img, H_img)

    const getColor = (value) => {
      const v = Math.max(-1, Math.min(1, value / maxVal))
      const hue = (1 - v) * 120
      const [r, g, b] = hsvToRgb(hue, 1, 1)
      const alpha = Math.floor(255 * Math.abs(v))
      return [r, g, b, alpha]
    }

    for (let i = 0; i < H_img; i++) {
      for (let j = 0; j < W_img; j++) {
        const val = smoothHeatmap[i][j]
        const index = (i * W_img + j) * 4
        const [r, g, b, a] = getColor(val)

        imageData.data[index] = r
        imageData.data[index + 1] = g
        imageData.data[index + 2] = b
        imageData.data[index + 3] = a
      }
    }

    ctx.putImageData(imageData, 0, 0)

    if (props.threshold > 0 && props.threshold < 1) {
      ctx.strokeStyle = 'white'
      ctx.lineWidth = 2
      for (let i = 1; i < H_img - 1; i++) {
        for (let j = 1; j < W_img - 1; j++) {
          const val = Math.abs(smoothHeatmap[i][j] / maxVal)
          if (Math.abs(val - props.threshold) < 0.01) {
            ctx.strokeRect(j - 1, i - 1, 2, 2)
          }
        }
      }
    }
  } else if (props.viewMode === 'Dots' || props.viewMode === 'Squares') {
    const maxVal = Math.max(...heatmap.flat().map(Math.abs)) || 1

    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = W
    tempCanvas.height = H
    const tempCtx = tempCanvas.getContext('2d')
    const imageData = tempCtx.createImageData(W, H)

    const getColor = (value) => {
      const v = Math.max(-1, Math.min(1, value / maxVal))
      const hue = (1 - v) * 120
      const [r, g, b, alpha] = hsvToRgb(hue, 1, 1).concat(Math.floor(255 * Math.abs(v)))
      return [r, g, b, alpha]
    }

    for (let i = 0; i < H; i++) {
      for (let j = 0; j < W; j++) {
        const val = heatmap[i][j]
        const index = (i * W + j) * 4
        const [r, g, b, a] = getColor(val)
        imageData.data.set([r, g, b, a], index)
      }
    }

    tempCtx.putImageData(imageData, 0, 0)

    ctx.imageSmoothingEnabled = props.viewMode === 'Dots'

    if (props.viewMode === 'Dots') {
      ctx.imageSmoothingQuality = 'high'
    }

    ctx.clearRect(0, 0, W_img, H_img)
    ctx.drawImage(tempCanvas, 0, 0, W_img, H_img)
  }

  const end = performance.now()
  const duration = end - start
  heatmapDurations.value.push(duration)
  console.log(`Heatmap draw took ${duration.toFixed(2)} ms`)
}

//only used for benchmarking
const exportDurations = () => {
  //simple JSON export for measuring heatmap performance
  const blob = new Blob([JSON.stringify(heatmapDurations.value)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'heatmap_durations.json'
  a.click()
  URL.revokeObjectURL(url)
}

const startBrush = (e) => {
  brushing.value = true
  brushStart.value = getCanvasCoordinates(e)
  brushEnd.value = null
  clearBrushOverlay()
}

const updateBrush = (e) => {
  if (!brushing.value) return
  brushEnd.value = getCanvasCoordinates(e)
  clearBrushOverlay()
  drawBrushOverlay()
}

const endBrush = () => {
  brushing.value = false
  if (brushStart.value && brushEnd.value) {
    emitMaskedAttributions()
  }
  drawHeatmap()
}

const getCanvasCoordinates = (e) => {
  const rect = brushCanvas.value.getBoundingClientRect()
  return {
    x: Math.floor(((e.clientX - rect.left) / rect.width) * brushCanvas.value.width),
    y: Math.floor(((e.clientY - rect.top) / rect.height) * brushCanvas.value.height),
  }
}

const clearBrushOverlay = () => {
  if (!brushCanvas.value) return
  const ctx = brushCanvas.value.getContext('2d')
  ctx.clearRect(0, 0, brushCanvas.value.width, brushCanvas.value.height)
}

const drawBrushOverlay = () => {
  if (!brushStart.value || !brushEnd.value || !brushCanvas.value) return

  const ctx = brushCanvas.value.getContext('2d')
  ctx.strokeStyle = 'rgba(0, 255, 0, 0.8)'
  ctx.lineWidth = 2
  ctx.setLineDash([5, 5])

  const x = Math.min(brushStart.value.x, brushEnd.value.x)
  const y = Math.min(brushStart.value.y, brushEnd.value.y)
  const w = Math.abs(brushEnd.value.x - brushStart.value.x)
  const h = Math.abs(brushEnd.value.y - brushStart.value.y)

  ctx.strokeRect(x, y, w, h)
  ctx.setLineDash([])
}

const emitMaskedAttributions = () => {
  const x1 = Math.min(brushStart.value.x, brushEnd.value.x)
  const x2 = Math.max(brushStart.value.x, brushEnd.value.x)
  const y1 = Math.min(brushStart.value.y, brushEnd.value.y)
  const y2 = Math.max(brushStart.value.y, brushEnd.value.y)

  const H = props.attributions[0].length
  const W = props.attributions[0][0].length

  const masked = props.attributions.map((map) => {
    const maskedMap = []
    for (let i = 0; i < H; i++) {
      maskedMap[i] = []
      for (let j = 0; j < W; j++) {
        const imgX = Math.floor((j / W) * brushCanvas.value.width)
        const imgY = Math.floor((i / H) * brushCanvas.value.height)

        if (imgX >= x1 && imgX <= x2 && imgY >= y1 && imgY <= y2) {
          maskedMap[i][j] = map[i][j]
        } else {
          maskedMap[i][j] = 0
        }
      }
    }
    return maskedMap
  })
  emit('brushed-selection', masked)
}

const clearBrush = () => {
  brushStart.value = null
  brushEnd.value = null
  clearBrushOverlay()

  drawHeatmap()

  //Emit original atrib
  emit('brushed-selection', props.attributions)
}

//Watch selection and update heatmap visbility
watch(
  () => props.selection,
  (newSelection) => {
    showHeatmap.value = newSelection.tokens_a.length === 0
    if (newSelection.tokens_a.length > 0) {
      brushStart.value = null
      brushEnd.value = null
      clearBrushOverlay()
    }
    drawHeatmap()
  },
  { deep: true },
)

//Redraw when attributions, threshold, or viewMode change
watch(
  () => [props.attributions, props.threshold, props.viewMode],
  () => {
    drawHeatmap()
  },
  { deep: true },
)

//stat stuff for benchmark, not used

let simulationActive = false
let simulationTimeout = null

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function runSimulationStep() {
  if (!simulationActive) return

  //Pick a random  selection
  const numTokens = props.attributions.length
  const numSelected = getRandomInt(1, numTokens) //not empty

  const randomIndices = []
  while (randomIndices.length < numSelected) {
    const idx = getRandomInt(0, numTokens - 1)
    if (!randomIndices.includes(idx)) {
      randomIndices.push(idx)
    }
  }

  props.selection.tokens_a = randomIndices

  //next step with random delay
  const delay = getRandomInt(200, 2000)
  simulationTimeout = setTimeout(runSimulationStep, delay)
}

function startSimulation() {
  if (simulationActive) return
  simulationActive = true
  runSimulationStep()
}

function stopSimulation() {
  simulationActive = false
  if (simulationTimeout) {
    clearTimeout(simulationTimeout)
    simulationTimeout = null
  }
}

onUnmounted(() => {
  stopSimulation()
})
</script>

<style scoped>
.image-wrapper {
  position: relative;
}
.image-wrapper img {
  display: block;
  width: 512px;
  height: 512px;
  object-fit: contain;
  transition: filter 0.3s ease;
}

.image-wrapper img.grayscale {
  filter: grayscale(100%);
}

.heatmap-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}
</style>
