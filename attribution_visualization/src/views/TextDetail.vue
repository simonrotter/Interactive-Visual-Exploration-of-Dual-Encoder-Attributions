<template>
  <div>
    <div
      class="bg-neutral-100 dark:bg-[rgb(49,49,49)] fixed p-2.5 z-[1000] w-full top-0 flex items-center"
    >
      <p
        @click="router.push({ name: 'image' })"
        class="ml-10 bg-neutral-200 dark:bg-neutral-700 pt-1 pb-1 pl-2 pr-2 rounded-lg cursor-pointer font-bold"
      >
        Image Analysis
      </p>
      <MultitextToggle
        v-if="hasResults"
        v-model="combineTokensToWords"
        :labels="['Tokens', 'Words', 'Words + Punctuation']"
        @change="combineTokensToWords > 0 ? (removeSpecialTokens = 1) : null"
        class="ml-5"
      />
      <MultitextToggle
        v-if="hasResults"
        v-model="removeSpecialTokens"
        :disabled="disableEOSsetting"
        :labels="['CLS/EOS', 'none']"
        class="ml-3"
      />
      <MultitextToggle
        v-if="hasResults"
        v-model="advancedView"
        :labels="['Simple', 'Advanced']"
        class="ml-3 mr-10"
      />
    </div>

    <!-- Input Section -->
    <div v-if="!hasResults" class="mt-24 mx-10 max-w-4xl">
      <h2 class="text-2xl font-bold mb-4">Text Attribution Analysis</h2>
      <p class="mb-4 text-neutral-600 dark:text-neutral-400">
        Enter two texts to analyze how tokens in the first text attribute to tokens in the second
        text.
      </p>

      <div class="space-y-4">
        <div>
          <label class="block mb-2 font-semibold">Text A (Source):</label>
          <textarea
            v-model="textA"
            placeholder="Enter first text here..."
            class="w-full h-32 p-3 border-2 border-neutral-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 resize-none"
            :class="{ 'border-red-500': errors.textA }"
          ></textarea>
          <p v-if="errors.textA" class="text-red-500 text-sm mt-1">{{ errors.textA }}</p>
        </div>

        <div>
          <label class="block mb-2 font-semibold">Text B (Target):</label>
          <textarea
            v-model="textB"
            placeholder="Enter second text here..."
            class="w-full h-32 p-3 border-2 border-neutral-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 resize-none"
            :class="{ 'border-red-500': errors.textB }"
          ></textarea>
          <p v-if="errors.textB" class="text-red-500 text-sm mt-1">{{ errors.textB }}</p>
        </div>

        <div class="flex gap-3">
          <button
            @click="analyzeTexts"
            :disabled="loading"
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
    <div v-if="hasResults" style="margin-top: 100px">
      <div class="mx-10 mb-4 flex gap-2">
        <button
          @click="resetAnalysis"
          class="px-4 py-2 bg-neutral-300 dark:bg-neutral-700 hover:bg-neutral-400 dark:hover:bg-neutral-600 rounded-lg font-semibold transition-colors"
        >
          ← New Analysis
        </button>
      </div>

      <div v-if="advancedView == 1">
        <div style="display: flex">
          <TwoDChart
            ref="attributionChart"
            :attributionModel="textTokenModel"
            :bounds="histogramBounds"
            :negativeBounds="histogramNegativeBounds"
            :selection="selectedTokens"
            @selection-changed="handleSelectionChanged"
            class="mr-16"
          />
          <HistogramSlider
            :histogramData="textTokenModel?.attributions ?? []"
            @range-changed="handleRangeChanged"
            @negative-range-changed="handleNegativeHistogramBoundsChanged"
          />
        </div>
      </div>
      <div style="margin-left: 70px; margin-top: 20px">
        <InteractiveText
          :tokenModel="textTokenModel"
          :selection="selectedTokens"
          :showReverseAttrib="advancedView == 1 && showReverseAttribution == 1"
          @selection-changed="handleSelectionChanged"
        />
        <div class="flex mt-2">
          <button
            @click="handleSelectionChanged({ tokens_a: [], tokens_b: [] })"
            class="clear-btn py-1 px-3 m-1 mt-2 bg-neutral-300 dark:bg-neutral-700 border-none rounded-[11px] cursor-pointer"
          >
            Remove Selection
          </button>
          <MultitextToggle
            class="py-1 mt-1 ml-1"
            v-if="advancedView == 1"
            v-model="showReverseAttribution"
            :labels="['Direct', 'Direct+Indirect']"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  fetchAttributions,
  fetchWordTokens,
  fetchWordcombinationTokens,
  fetchPos,
  fetchCombinationPos,
} from '../js/backendUtils.js'
import { deleteSpecialTokens } from '@/js/utils.js'
import HistogramSlider from '../components/HistogramSlider.vue'
import InteractiveText from '@/components/InteractiveText.vue'
import MultitextToggle from '@/components/MultitextToggle.vue'
import TwoDChart from '@/components/2dChart.vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const attributionChart = ref()

// Input state
const textA = ref('')
const textB = ref('')
const loading = ref(false)
const error = ref(null)
const errors = ref({ textA: '', textB: '' })
const hasResults = ref(false)

// UI state
const disableEOSsetting = ref(true)
const combineTokensToWords = ref(1)
const removeSpecialTokens = ref(1)
const advancedView = ref(1)
const showReverseAttribution = ref(0)
const selectedAttributionModel = ref(null)

const histogramBounds = ref({ left: -1, right: 1 })
const histogramNegativeBounds = ref({ left: 0, right: 0 })

const textTokenModel = computed(() => {
  if (selectedAttributionModel.value) {
    let preparedTokenModel = prepareTokenmodel(selectedAttributionModel.value)
    return preparedTokenModel || {}
  }
  return {}
})

function prepareTokenmodel(tokenModel) {
  if (combineTokensToWords.value == 1) {
    tokenModel = tokenModel.word ?? tokenModel
  } else if (combineTokensToWords.value == 2) {
    tokenModel = tokenModel.wordcombinations ?? tokenModel
  }
  if (removeSpecialTokens.value == 1) {
    tokenModel = deleteSpecialTokens(tokenModel)
  }
  return tokenModel
}

function validateInputs() {
  errors.value = { textA: '', textB: '' }
  let isValid = true

  if (!textA.value.trim()) {
    errors.value.textA = 'Text A is required'
    isValid = false
  }
  if (!textB.value.trim()) {
    errors.value.textB = 'Text B is required'
    isValid = false
  }

  return isValid
}

async function analyzeTexts() {
  if (!validateInputs()) return

  loading.value = true
  error.value = null
  hasResults.value = false

  try {
    // Fetch all required data
    selectedAttributionModel.value = await fetchAttributions(textA.value, textB.value)
    await addWordAttributes(textA.value, textB.value)
    await addWordCombinationAttributes(textA.value, textB.value)
    await addPosTags(textA.value, textB.value)
    await addCombinationPosTags(textA.value, textB.value)

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
  selectedAttributionModel.value = null
  selectedTokens.value = { tokens_a: [], tokens_b: [] }
  error.value = null
}

async function addWordAttributes(textA, textB) {
  const combinations = await fetchWordTokens(textA, textB)
  selectedAttributionModel.value.word ??= {}
  selectedAttributionModel.value.word.tokens_a = combinations.tokens_a
  selectedAttributionModel.value.word.tokens_b = combinations.tokens_b
  selectedAttributionModel.value.word.attributions = combinations.attributions
  selectedAttributionModel.value.word.text_a = selectedAttributionModel.value.text_a
  selectedAttributionModel.value.word.text_b = selectedAttributionModel.value.text_b
}

async function addPosTags(textA, textB) {
  const pos = await fetchPos(textA, textB)
  selectedAttributionModel.value.word ??= {}
  selectedAttributionModel.value.word.tokens_a_categorized = pos.tokens_a_categorized
  selectedAttributionModel.value.word.tokens_b_categorized = pos.tokens_b_categorized
}

async function addWordCombinationAttributes(textA, textB) {
  const combinations = await fetchWordcombinationTokens(textA, textB)
  selectedAttributionModel.value.wordcombinations ??= {}
  selectedAttributionModel.value.wordcombinations.tokens_a = combinations.tokens_a
  selectedAttributionModel.value.wordcombinations.tokens_b = combinations.tokens_b
  selectedAttributionModel.value.wordcombinations.attributions = combinations.attributions
  selectedAttributionModel.value.wordcombinations.text_a = selectedAttributionModel.value.text_a
  selectedAttributionModel.value.wordcombinations.text_b = selectedAttributionModel.value.text_b
}

async function addCombinationPosTags(textA, textB) {
  const pos = await fetchCombinationPos(textA, textB)
  selectedAttributionModel.value.wordcombinations ??= {}
  selectedAttributionModel.value.wordcombinations.tokens_a_categorized = pos.tokens_a_categorized
  selectedAttributionModel.value.wordcombinations.tokens_b_categorized = pos.tokens_b_categorized
}

function handleRangeChanged(bounds) {
  histogramBounds.value.left = bounds.left
  histogramBounds.value.right = bounds.right
}

function handleNegativeHistogramBoundsChanged(bounds) {
  histogramNegativeBounds.value.left = bounds.left
  histogramNegativeBounds.value.right = bounds.right
}

const selectedTokens = ref({ tokens_a: [], tokens_b: [] })

function handleSelectionChanged(emittedSelection) {
  selectedTokens.value.tokens_a = emittedSelection.tokens_a
  selectedTokens.value.tokens_b = emittedSelection.tokens_b
}

watch(
  combineTokensToWords,
  () => {
    selectedTokens.value = { tokens_a: [], tokens_b: [] }
    if (combineTokensToWords.value > 0) {
      disableEOSsetting.value = true
    } else {
      disableEOSsetting.value = false
    }
  },
  { deep: true },
)

watch(
  () => [combineTokensToWords.value, removeSpecialTokens.value],
  () => {
    selectedTokens.value = { tokens_a: [], tokens_b: [] }
  },
  { deep: true },
)
</script>

<style scoped>
textarea:focus {
  outline: none;
  border-color: #3b82f6;
}
</style>
