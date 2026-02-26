<template>
  <div>
    <div
      class="bg-neutral-100 dark:bg-[rgb(49,49,49)] fixed p-2.5 z-[1000] w-full top-0 flex items-center"
    >
      <p
        @click="router.push({ name: 'text' })"
        class="ml-10 bg-neutral-200 dark:bg-neutral-700 pt-1 pb-1 pl-2 pr-2 rounded-lg cursor-pointer font-bold"
      >
        Text Analysis
      </p>
      <MultitextToggle
        v-if="hasResults"
        v-model="advancedView"
        :labels="['Simple', 'Advanced']"
        class="ml-3 mr-3"
      />
      <MultitextToggle
        v-if="hasResults"
        v-model="viewModeIndex"
        :labels="['Squares', 'Dots', 'Interpolated']"
        class="mr-10"
      />
      <MultitextToggle
        v-if="hasResults"
        v-model="grayscaleMode"
        :labels="['Color', 'Grayscale']"
        class="mr-10"
      />
    </div>

    <!-- Input Section -->
    <div v-if="!hasResults" class="mt-24 mx-10 max-w-4xl">
      <h2 class="text-2xl font-bold mb-4">Image Attribution Analysis</h2>
      <p class="mb-4 text-neutral-600 dark:text-neutral-400">
        Upload an image and provide a caption to analyze token attributions to image regions.
      </p>

      <div class="space-y-4">
        <div>
          <label class="block mb-2 font-semibold">Image:</label>
          <div
            class="border-2 border-dashed border-neutral-300 dark:border-neutral-600 rounded-lg p-8 text-center"
            :class="{ 'border-red-500': errors.image, 'border-blue-500': dragOver }"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              class="hidden"
            />

            <div v-if="!previewUrl">
              <svg
                class="mx-auto h-12 w-12 text-neutral-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <p class="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
                Drag and drop an image here, or
                <button
                  @click="$refs.fileInput.click()"
                  class="text-blue-600 hover:text-blue-700 font-semibold"
                >
                  browse
                </button>
              </p>
              <p class="text-xs text-neutral-500 mt-1">PNG, JPG</p>
            </div>

            <div v-else class="relative">
              <img :src="previewUrl" alt="Preview" class="max-h-64 mx-auto rounded-lg" />
              <button
                @click="clearImage"
                class="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-2"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>
          <p v-if="errors.image" class="text-red-500 text-sm mt-1">{{ errors.image }}</p>
        </div>

        <div>
          <label class="block mb-2 font-semibold">Caption:</label>
          <input
            v-model="caption"
            type="text"
            placeholder="Enter an image caption"
            class="w-full p-3 border-2 border-neutral-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800"
          />
        </div>

        <div class="flex gap-3">
          <button
            @click="analyzeImage"
            :disabled="loading || !selectedFile || !caption.length > 0"
            class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-400 text-white rounded-lg font-semibold transition-colors"
          >
            {{ loading ? 'Analyzing...' : 'Analyze' }}
          </button>
          <button
            v-if="hasResults"
            @click="resetAnalysis"
            class="px-6 py-2 bg-neutral-300 dark:bg-neutral-700 hover:bg-neutral-400 dark:hover:bg-neutral-600 rounded-lg font-semibold transition-colors"
          >
            New Analysis
          </button>
        </div>

        <div v-if="loading" class="flex items-center gap-2 text-neutral-600 dark:text-neutral-400">
          <div
            class="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full"
          ></div>
          <span>Computing attributions...</span>
        </div>

        <div
          v-if="error"
          class="p-4 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 rounded-lg"
        >
          <p class="text-red-800 dark:text-red-200 font-semibold">Error:</p>
          <p class="text-red-700 dark:text-red-300">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="hasResults" style="margin-top: 100px; margin-left: 60px">
      <div class="mb-4 flex gap-2">
        <button
          @click="resetAnalysis"
          class="px-4 py-2 bg-neutral-300 dark:bg-neutral-700 hover:bg-neutral-400 dark:hover:bg-neutral-600 rounded-lg font-semibold transition-colors"
        >
          ← New Analysis
        </button>
      </div>

      <div style="display: flex">
        <div>
          <ImageHeatmap
            :imageUrl="imageUrl"
            :viewMode="viewMode"
            :grayscale="grayscale"
            :attributions="filteredAttributions"
            :selection="selection"
            :threshold="threshold"
            @brushed-selection="onBrushedAttributions"
          />
        </div>
        <div
          style="width: 450px"
          class="gap-10 bg-neutral-200 dark:bg-neutral-700 p-2 rounded-[15px] ml-10 pos-panel-wrapper"
          @mousedown.stop
          @mouseup.stop
          @click.stop
        >
          <div v-if="advancedView == 1">
            <PosSelector
              :attributionModel="tokenModel"
              :collapsed="collapsedPos"
              @update:collapsed="onCollapsedUpdate"
            />
            <PosChart
              :attributionModel="tokenModel"
              :collapsed="collapsedPos"
              style="max-height: 120px; max-width: 500px"
              @update:collapsed="onCollapsedUpdate"
            />
          </div>
        </div>
        <HistogramSlider
          v-if="advancedView == 1"
          class="ml-10"
          :histogramData="attributionMaps"
          @range-changed="handleRangeChanged"
          @negative-range-changed="handleNegativeHistogramBoundsChanged"
          @range-handle-active="handleRangeSliderActivitychange"
        />
      </div>
      <div>
        <FancySlider
          v-if="advancedView == 1"
          v-model="threshold"
          :min="0"
          :max="1"
          :step="0.01"
          :text="`Threshold: ${threshold}`"
          class="mt-6 w-[500px] h-[24px]"
          :color="attributionSliderColor"
        />
        <TextChart
          :tokenModel="tokenModel"
          :selection="selection"
          :imageAttributions="brushedAttributions"
          :showcolors="showTextColors"
          @selection-changed="updateSelection"
          class="mt-6"
        />
        <div class="flex mt-2">
          <button
            @click="updateSelection({ tokens_a: [] })"
            class="clear-btn py-1 px-3 m-1 mt-2 bg-neutral-300 dark:bg-neutral-700 border-none rounded-[11px] cursor-pointer"
          >
            Remove Selection
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import TextChart from '../components/InteractiveImageText.vue'
import ImageHeatmap from '../components/ImageHeatmap.vue'
import HistogramSlider from '../components/HistogramSlider.vue'
import PosSelector from '../components/PosSelector.vue'
import PosChart from '../components/PosChart.vue'
import { ref, computed } from 'vue'
import { are3DArraysEqual } from '../js/utils'
import MultitextToggle from '../components/MultitextToggle.vue'
import { useRouter } from 'vue-router'
import FancySlider from '../components/FancySlider.vue'
import { fetchImageAttribution } from '../js/backendUtils.js'

const router = useRouter()

// Input state
const selectedFile = ref(null)
const previewUrl = ref(null)
const caption = ref('')
const loading = ref(false)
const error = ref(null)
const errors = ref({ image: '' })
const hasResults = ref(false)
const dragOver = ref(false)
const fileInput = ref(null)

// UI state
const threshold = ref(1)
const selection = ref({ tokens_a: [], tokens_b: [] })
const tokenModel = ref(null)
const imageUrl = ref('')
const attributionMaps = ref([])
const showTextColors = ref(false)
const heatmapBrushExists = ref(false)
const attributionSliderColor = ref()
const advancedView = ref(1)
const viewModeIndex = ref(2)
const grayscaleMode = ref(0)
const brushedSelection = ref([])
const positiveBounds = ref({ left: -1, right: 1 })
const positiveBoundsIntermediate = ref({ left: -1, right: 1 })
const negativeBounds = ref({ left: 0, right: 0 })
const histogramSliderActive = ref(false)

const collapsedPos = ref({ rows: [], columns: [] })

const viewMode = computed(() => {
  const modes = ['Squares', 'Dots', 'Interpolated']
  return modes[viewModeIndex.value] || 'Interpolated'
})

const grayscale = computed(() => {
  return grayscaleMode.value === 1
})

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    processFile(file)
  }
}

function handleDrop(event) {
  dragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    processFile(file)
  }
}

function processFile(file) {
  if (file.size > 10 * 1024 * 1024) {
    errors.value.image = 'File size must be less than 10MB'
    return
  }

  selectedFile.value = file
  errors.value.image = ''

  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target.result
  }
  reader.readAsDataURL(file)
}

function clearImage() {
  selectedFile.value = null
  previewUrl.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function analyzeImage() {
  if (!selectedFile.value) {
    errors.value.image = 'Please select an image'
    return
  }

  loading.value = true
  error.value = null
  hasResults.value = false

  try {
    const data = await fetchImageAttribution(selectedFile.value, caption.value)

    // Reduce num_tokens, h, w to only num_tokens
    const tokenAttributions = data.attributions.map((heatmap) =>
      heatmap.flat().reduce((acc, val) => acc + val, 0),
    )

    // Convert to 2D format for compatibility with PosChart
    const attributionMatrix = tokenAttributions.map((val) => [val])

    tokenModel.value = {
      tokens_a: data.tokens,
      tokens_b: [],
      tokens_a_categorized: data.tokens_categorized,
      tokens_b_categorized: [],
      attributions: attributionMatrix,
    }

    attributionMaps.value = data.attributions
    imageUrl.value = `http://${window.location.hostname}:80${data.image_url}`

    hasResults.value = true
  } catch (err) {
    error.value = err.message
    console.error('Analysis error:', err)
  } finally {
    loading.value = false
  }
}

function resetAnalysis() {
  hasResults.value = false
  clearImage()
  caption.value = ''
  tokenModel.value = null
  attributionMaps.value = []
  imageUrl.value = ''
  selection.value = { tokens_a: [], tokens_b: [] }
  collapsedPos.value = { rows: [], columns: [] }
  error.value = null
}

function onCollapsedUpdate(newCollapsed) {
  collapsedPos.value = newCollapsed
  const model = tokenModel.value
  const categorized = model?.tokens_a_categorized || []
  const totalTokens = categorized.length

  const collapsedSet = new Set(newCollapsed.rows)
  if (collapsedSet.size === tokenModel.value.tokens_a.length) {
    selection.value.tokens_a = []
    if (heatmapBrushExists.value) {
      showTextColors.value = true
    }
    attributionSliderColor.value = '#6e6e6e'
  } else {
    const selected = []
    for (let i = 0; i < totalTokens; i++) {
      if (!collapsedSet.has(i)) selected.push(i)
    }
    selection.value.tokens_a = selected
    showTextColors.value = false
    heatmapBrushExists.value = false
    attributionSliderColor.value = null
  }
}

const onBrushedAttributions = (maskedAttributions) => {
  if (maskedAttributions) {
    brushedSelection.value = maskedAttributions
    if (!are3DArraysEqual(maskedAttributions, filteredAttributions.value)) {
      showTextColors.value = true
      heatmapBrushExists.value = true
      attributionSliderColor.value = '#6e6e6e'
    } else {
      showTextColors.value = false
      heatmapBrushExists.value = false
      attributionSliderColor.value = null
    }
  }
}

async function handleRangeSliderActivitychange(isActive) {
  if (histogramSliderActive.value && !isActive) {
    let currentSelection = selection.value
    positiveBounds.value = positiveBoundsIntermediate.value
    setTimeout(function () {
      updateSelection(currentSelection)
    }, 150)
  }
  histogramSliderActive.value = isActive
}

function handleRangeChanged(bounds) {
  positiveBoundsIntermediate.value = bounds
  if (!histogramSliderActive.value) {
    let currentSelection = selection.value
    positiveBounds.value = positiveBoundsIntermediate.value
    setTimeout(function () {
      updateSelection(currentSelection)
    }, 150)
  }
}

function handleNegativeHistogramBoundsChanged(bounds) {
  if (!histogramSliderActive.value) {
    let currentSelection = selection.value
    negativeBounds.value = bounds
    setTimeout(function () {
      updateSelection(currentSelection)
    }, 150)
  }
}

const updateSelection = (newSelection) => {
  selection.value = newSelection
  if (newSelection.tokens_a.length > 0) {
    showTextColors.value = false
    heatmapBrushExists.value = false
    attributionSliderColor.value = null
  } else {
    if (heatmapBrushExists.value) {
      showTextColors.value = true
    }
    attributionSliderColor.value = '#6e6e6e'
  }
  const model = tokenModel.value
  if (!model) return
  const totalTokens = model.tokens_a?.length || 0
  const selectedSet = new Set(newSelection.tokens_a)
  let collapsed = []
  for (let i = 0; i < totalTokens; i++) {
    if (!selectedSet.has(i)) {
      collapsed.push(i)
    }
  }
  collapsedPos.value = {
    ...collapsedPos.value,
    rows: collapsed,
  }
}

const filteredAttributions = computed(() => {
  if (!attributionMaps.value.length) return []
  return attributionMaps.value.map((channel) =>
    channel.map((row) =>
      row.map((val) => {
        if (val < positiveBounds.value.left || val > positiveBounds.value.right) {
          return 0
        }
        if (val >= negativeBounds.value.left && val <= negativeBounds.value.right) {
          return 0
        }
        return val
      }),
    ),
  )
})

const brushedAttributions = computed(() => {
  if (!brushedSelection.value.length) {
    brushedSelection.value = filteredAttributions.value
  }
  return brushedSelection.value.map((channel) =>
    channel.map((row) =>
      row.map((val) => {
        if (val < positiveBounds.value.left || val > positiveBounds.value.right) {
          return 0
        }
        if (val >= negativeBounds.value.left && val <= negativeBounds.value.right) {
          return 0
        }
        return val
      }),
    ),
  )
})
</script>

<style scoped>
input[type='file']:focus + label {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
