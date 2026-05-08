<template>
  <div>
    <div
      class="bg-neutral-100 dark:bg-[rgb(49,49,49)] fixed p-2.5 z-[1000] w-full top-0 flex items-center"
    >
      <p
        @click="router.push({ name: 'overview' })"
        class="ml-10 bg-neutral-200 dark:bg-neutral-700 pt-1 pb-1 pl-2 pr-2 rounded-lg cursor-pointer font-bold"
      >
        Overview
      </p>
      <MultitextToggle
        v-model="combineTokensToWords"
        :labels="['Tokens', 'Words', 'Words + Punctuation']"
        @change="combineTokensToWords > 0 ? (removeSpecialTokens = 1) : null"
        class="ml-5"
      />
      <MultitextToggle
        v-model="removeSpecialTokens"
        :disabled="disableEOSsetting"
        :labels="['CLS/EOS', 'none']"
        class="ml-3"
      />
      <MultitextToggle v-model="advancedView" :labels="['Simple', 'Advanced']" class="ml-3 mr-10" />

      <span ref="textSizer" class="text-sizer">{{ textPairs[selectedIndex]?.text_a }}</span>
      <select
        v-model="selectedIndex"
        @change="updateTextByIndex(selectedIndex)"
        :style="selectStyle"
        class="bg-neutral-200 dark:bg-neutral-700"
      >
        <option v-for="(pair, index) in textPairs" :key="index" :value="index">
          {{ pair.text_a }}
        </option>
      </select>
    </div>
    <div style="margin-top: 100px">
      <div>
        <div style="display: flex">
          <TwoDChart
            ref="attributionChart"
            :attributionModel="textTokenModel"
            :bounds="histogramBounds"
            :negativeBounds="histogramNegativeBounds"
            :selection="selectedTokens"
            :advancedView="advancedView"
            @selection-changed="handleSelectionChanged"
            class="mr-16"
          />

          <HistogramSlider
            v-if="advancedView == 1"
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

      <p>
        {{ availablePos }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, defineEmits } from 'vue'
import {
  fetchTexts,
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
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()

const attributionChart = ref()

const textPairs = ref([])
const route = useRoute()
const selectedIndex = ref(route.params.id)
//header text automatic sizing
const textSizer = ref(null)
const selectWidth = ref(200)

const disableEOSsetting = ref(true)

const combineTokensToWords = ref(1)
const removeSpecialTokens = ref(1)
const advancedView = ref(1)
const showReverseAttribution = ref(0)
const selectedAttributionModel = ref()

//browser dark/lighmode check
const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  isDarkMode.value = e.matches
})

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

//helpers to update 2d chart when histogram changed
function handleRangeChanged(bounds) {
  histogramBounds.value.left = bounds.left
  histogramBounds.value.right = bounds.right
}

function handleNegativeHistogramBoundsChanged(bounds) {
  histogramNegativeBounds.value.left = bounds.left
  histogramNegativeBounds.value.right = bounds.right
}

//gets the text and attribution data from backend
const loadTexts = async () => {
  try {
    const data = await fetchTexts()
    textPairs.value = data

    if (textPairs.value.length > 0) {
      selectedAttributionModel.value = await fetchAttributions(selectedIndex.value)
      await addWordAttributes(selectedIndex.value)
      await addWordCombinationAttributes(selectedIndex.value)
      await addPosTags(selectedIndex.value)
      await addCombinationPosTags(selectedIndex.value)
    }
  } catch (error) {
    console.error('Error fetching texts:', error)
  }
  updateSelectWidth()
}

onMounted(async () => {
  await loadTexts()
})

//construct a full attributionmodel from the fetched data
async function addWordAttributes(backendListIndex) {
  const combinations = await fetchWordTokens(backendListIndex)
  selectedAttributionModel.value.word ??= {}
  selectedAttributionModel.value.word.tokens_a = combinations.tokens_a
  selectedAttributionModel.value.word.tokens_b = combinations.tokens_b
  selectedAttributionModel.value.word.attributions = combinations.attributions
  selectedAttributionModel.value.word.text_a = selectedAttributionModel.value.text_a
  selectedAttributionModel.value.word.text_b = selectedAttributionModel.value.text_b
}

async function addPosTags(backendListIndex) {
  const pos = await fetchPos(backendListIndex)
  selectedAttributionModel.value.word ??= {}
  selectedAttributionModel.value.word.tokens_a_categorized = pos.tokens_a_categorized
  selectedAttributionModel.value.word.tokens_b_categorized = pos.tokens_b_categorized
}

async function addWordCombinationAttributes(backendListIndex) {
  const combinations = await fetchWordcombinationTokens(backendListIndex)
  selectedAttributionModel.value.wordcombinations ??= {}
  selectedAttributionModel.value.wordcombinations.tokens_a = combinations.tokens_a
  selectedAttributionModel.value.wordcombinations.tokens_b = combinations.tokens_b
  selectedAttributionModel.value.wordcombinations.attributions = combinations.attributions
  selectedAttributionModel.value.wordcombinations.text_a = selectedAttributionModel.value.text_a
  selectedAttributionModel.value.wordcombinations.text_b = selectedAttributionModel.value.text_b
}

async function addCombinationPosTags(backendListIndex) {
  const pos = await fetchCombinationPos(backendListIndex)
  selectedAttributionModel.value.wordcombinations ??= {}
  selectedAttributionModel.value.wordcombinations.tokens_a_categorized = pos.tokens_a_categorized
  selectedAttributionModel.value.wordcombinations.tokens_b_categorized = pos.tokens_b_categorized
}

//applies the width of the dummy measuringtext to the dropdown variable
const updateSelectWidth = () => {
  if (textSizer.value) {
    selectWidth.value = textSizer.value.offsetWidth
  }
}

//dynamic width in dropdown style
const selectStyle = computed(() => ({
  width: `${selectWidth.value + 20}px`,
  padding: '8px',
  borderRadius: '13px',
  border: 'solid 2px gray',
  transition: 'width .4s ease-in-out',
  outline: 'none',
}))

const selectedTokens = ref({ tokens_a: new Array(), tokens_b: new Array() })

async function updateTextByIndex(index) {
  router.push({ name: 'detail', params: { id: index } })
  selectedAttributionModel.value = await fetchAttributions(index)

  await addWordAttributes(index)
  await addWordCombinationAttributes(index)
  await addPosTags(index)
  await addCombinationPosTags(index)
  updateSelectWidth()
  selectedTokens.value = { tokens_a: new Array(), tokens_b: new Array() }
  attributionChart.value.collapseLowAttributionRowsAndColumns()
}

function handleSelectionChanged(emittedSelection) {
  selectedTokens.value.tokens_a = emittedSelection.tokens_a
  selectedTokens.value.tokens_b = emittedSelection.tokens_b
}

watch(
  combineTokensToWords,
  () => {
    selectedTokens.value = { tokens_a: new Array(), tokens_b: new Array() }
    if (combineTokensToWords.value > 0) {
      disableEOSsetting.value = true
    } else {
      disableEOSsetting.value = false
    }
  },
  { deep: true },
)

watch(
  () => [combineTokensToWords, removeSpecialTokens],
  () => {
    selectedTokens.value = { tokens_a: new Array(), tokens_b: new Array() }
  },
  { deep: true },
)

const emit = defineEmits(['switchViewMode'])
</script>

<style scoped>
/** dummy text for measureing width */
.text-sizer {
  position: absolute;
  visibility: hidden;
  white-space: nowrap;
  font-size: 16.8px;
  font-family: inherit;
  padding: 8px;
  border: 2px solid gray;
  border-radius: 13px;
}
</style>
