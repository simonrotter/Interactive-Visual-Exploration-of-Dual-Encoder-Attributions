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
      <MultitextToggle v-model="advancedView" :labels="['Simple', 'Advanced']" class="ml-3 mr-3" />
      <MultitextToggle
        v-model="viewModeIndex"
        :labels="['Squares', 'Dots', 'Interpolated']"
        class="mr-10"
      />
      <MultitextToggle v-model="grayscaleMode" :labels="['Color', 'Grayscale']" class="mr-10" />
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
    <div style="margin-top: 100px; margin-left: 60px">
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
          v-if="advancedView == 1"
        >
          <div>
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
import { ref, onMounted, computed } from 'vue'
import { are3DArraysEqual } from '../js/utils'
import MultitextToggle from '../components/MultitextToggle.vue'
import { useRoute, useRouter } from 'vue-router'
import FancySlider from '../components/FancySlider.vue'

const router = useRouter()
const route = useRoute()
const selectedIndex = ref(route.params.id)

const threshold = ref(1) //initial threshold showing no line

const selection = ref({ tokens_a: [], tokens_b: [] })
const tokenModel = ref(null)
const imageUrl = ref('')
const attributionMaps = ref([])
const textSizer = ref(null)
const selectWidth = ref(200)
const showTextColors = ref(false)
const heatmapBrushExists = ref(false)
const attributionSliderColor = ref()

const advancedView = ref(1)
const viewModeIndex = ref(2) // Default to 'Interpolated' (index 2)
const grayscaleMode = ref(0) // 0 = Color, 1 = Grayscale
const brushedSelection = ref([])
const positiveBounds = ref({ left: -1, right: 1 })
const positiveBoundsIntermediate = ref({ left: -1, right: 1 })
const negativeBounds = ref({ left: 0, right: 0 })
const histogramSliderActive = ref(false)

const textPairs = ref([])

const getApiBase = () => {
  if (window.location.port === '8020') {
    return '' // same origin, use relative URLs
  }
  return `http://${window.location.hostname}:8020`
}

const apiBase = getApiBase()

// Computed property to convert viewModeIndex to viewMode string
const viewMode = computed(() => {
  const modes = ['Squares', 'Dots', 'Interpolated']
  return modes[viewModeIndex.value] || 'Interpolated'
})

// Computed property to convert grayscaleMode to boolean
const grayscale = computed(() => {
  return grayscaleMode.value === 1
})

const updateTextByIndex = (idx) => {
  router.push({ name: 'image', params: { id: idx } })
  selectedIndex.value = idx
  loadImgAttribs(idx)
}

const fetchAllImageTexts = async () => {
  try {
    const response = await fetch(`${apiBase}/imageAttributions`)
    if (!response.ok) throw new Error('Failed to fetch image captions')
    const data = await response.json()
    textPairs.value = data.map((d) => ({
      index: d.index,
      text_a: d.caption, //caption is text_a from interactive text (we reuse the text text attrib text component)
    }))
  } catch (error) {
    console.error('Fetching captions failed:', error)
  }
}

const collapsedPos = ref({ rows: [], columns: [] })

function onCollapsedUpdate(newCollapsed) {
  collapsedPos.value = newCollapsed

  const model = tokenModel.value
  const categorized = model?.tokens_a_categorized || []
  const totalTokens = categorized.length

  //Determine which POS tokens are still visible, not colapsed
  const collapsedSet = new Set(newCollapsed.rows)

  if (collapsedSet.size === tokenModel.value.tokens_a.length) {
    //all are collapsed
    selection.value.tokens_a = []
    if (heatmapBrushExists.value) {
      showTextColors.value = true
    }
    attributionSliderColor.value = '#6e6e6e'
  } else {
    //highlight non collapsed indices
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
//histogram handle click change
async function handleRangeSliderActivitychange(isActive) {
  if (histogramSliderActive.value && !isActive) {
    let currentSelection = selection.value
    positiveBounds.value = positiveBoundsIntermediate.value
    setTimeout(function () {
      updateSelection(currentSelection) //reuse to load selection again after user stopped moving histogram
    }, 150)
  }
  histogramSliderActive.value = isActive
}

//those trggerif user brushes negative or clicks a shortcut button
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

  //Otherwise, collapsed are those NOT selected
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

const loadImgAttribs = async (idx = 0) => {
  try {
    const response = await fetch(`${apiBase}/imageAttributions/${idx}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    //Reduce num_tokens mh,w to only num_tokens
    const tokenAttributions = data.attributions.map((heatmap) =>
      heatmap.flat().reduce((acc, val) => acc + val, 0),
    )

    //Convert to 2D format for compatibility with PosChart
    const attributionMatrix = tokenAttributions.map((val) => [val])

    tokenModel.value = {
      tokens_a: data.tokens,
      tokens_b: [],
      tokens_a_categorized: data.tokens_categorized,
      tokens_b_categorized: [],
      attributions: attributionMatrix,
    }

    attributionMaps.value = data.attributions //still keep original for heatmaps
    imageUrl.value = `${apiBase}${data.image_url}`
  } catch (error) {
    console.error('Daten laden fehlgeschlagen: ' + error.message)
  }
  updateSelectWidth()
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

const updateSelectWidth = () => {
  if (textSizer.value) {
    selectWidth.value = textSizer.value.offsetWidth
  }
}

const selectStyle = computed(() => ({
  width: `${selectWidth.value + 20}px`,
  padding: '8px',
  borderRadius: '13px',
  border: 'solid 2px gray',
  transition: 'width .4s ease-in-out',
  outline: 'none',
}))

onMounted(async () => {
  await fetchAllImageTexts()
  if (textPairs.value.length > 0) {
    loadImgAttribs(selectedIndex.value)
  }
})
</script>
<style>
/** dummy text for measureing width */
.text-sizer {
  position: absolute;
  visibility: hidden;
  white-space: nowrap;
  font-size: 16.8px;
  font-family: inherit;
  padding: 8px;
  border: 2px solid gray;
}
</style>
