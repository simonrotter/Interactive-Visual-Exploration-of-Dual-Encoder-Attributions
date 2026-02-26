<template>
  <div v-if="categories.length > 0">
    <StateToggle
      v-for="cat in categories"
      :key="cat"
      :label="getPOSDisplayName(cat)"
      :state="getToggleState(cat)"
      @toggle="toggleCategory(cat)"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { getPOSDisplayName } from '../js/posUtils.js'
import StateToggle from './3StateToggle.vue'

const props = defineProps({
  attributionModel: Object,
  collapsed: Object,
  preventAllDeselect: (Boolean = true),
})

const emit = defineEmits(['update:collapsed'])

function getToggleState(cat) {
  if (isFullyVisible(cat)) return 'checked'
  if (isFullyCollapsed(cat)) return 'unchecked'
  return 'indeterminate'
}

const categories = ref([])
const checkedCategories = ref({})
const checkboxRefs = ref({})

function buildCategoryIndexMap() {
  const model = props.attributionModel || {}
  const aCats = Array.isArray(model.tokens_a_categorized) ? model.tokens_a_categorized : []
  const bCats = Array.isArray(model.tokens_b_categorized) ? model.tokens_b_categorized : []

  const map = {}
  aCats.forEach((cat, i) => {
    if (!cat) return
    if (!map[cat]) map[cat] = { aIndices: new Set(), bIndices: new Set() }
    map[cat].aIndices.add(i)
  })
  bCats.forEach((cat, i) => {
    if (!cat) return
    if (!map[cat]) map[cat] = { aIndices: new Set(), bIndices: new Set() }
    map[cat].bIndices.add(i)
  })
  return map
}

function isFullyCollapsed(cat) {
  const map = buildCategoryIndexMap()
  const entry = map[cat]
  if (!entry) return false
  const { aIndices, bIndices } = entry
  return (
    [...aIndices].every((i) => props.collapsed.rows.includes(i)) &&
    [...bIndices].every((i) => props.collapsed.columns.includes(i))
  )
}

function isFullyVisible(cat) {
  const map = buildCategoryIndexMap()
  const entry = map[cat]
  if (!entry) return true
  const { aIndices, bIndices } = entry
  return (
    [...aIndices].every((i) => !props.collapsed.rows.includes(i)) &&
    [...bIndices].every((i) => !props.collapsed.columns.includes(i))
  )
}

function isPartial(cat) {
  return !isFullyVisible(cat) && !isFullyCollapsed(cat)
}

function updateAllIndeterminateStates() {
  nextTick(() => {
    categories.value.forEach((cat) => {
      const el = checkboxRefs.value[cat]
      if (el) {
        el.indeterminate = isPartial(cat)
      }
    })
  })
}

function toggleCategory(cat) {
  const map = buildCategoryIndexMap()
  const entry = map[cat]
  if (!entry) return

  const { aIndices, bIndices } = entry
  const rowsSet = new Set(props.collapsed.rows)
  const colsSet = new Set(props.collapsed.columns)

  if (isFullyVisible(cat)) {
    const stillVisibleCats = categories.value.filter((c) => c !== cat && isFullyVisible(c))
    if (props.preventAllDeselect && stillVisibleCats.length === 0) {
      //prevent collapsing the last visible category
      nextTick(() => {
        const el = checkboxRefs.value[cat]
        if (el) {
          el.checked = true
          el.indeterminate = false
        }
      })
      return
    }
    aIndices.forEach((i) => rowsSet.add(i))
    bIndices.forEach((i) => colsSet.add(i))
  } else {
    aIndices.forEach((i) => rowsSet.delete(i))
    bIndices.forEach((i) => colsSet.delete(i))
  }

  emit('update:collapsed', {
    rows: Array.from(rowsSet),
    columns: Array.from(colsSet),
  })
}

//pdate categories for new models
watch(
  () => props.attributionModel,
  (model) => {
    const aCats = Array.isArray(model?.tokens_a_categorized) ? model.tokens_a_categorized : []
    const bCats = Array.isArray(model?.tokens_b_categorized) ? model.tokens_b_categorized : []

    if (!aCats.length && !bCats.length) {
      categories.value = []
      return
    }

    categories.value = Array.from(new Set([...aCats, ...bCats]))
  },
  { immediate: true, deep: true },
)

watch(
  categories,
  (newCategories) => {
    checkedCategories.value = {}
    newCategories.forEach((cat) => {
      checkedCategories.value[cat] = true
    })
  },
  { immediate: true },
)

watch(
  () => [props.collapsed.rows.slice(), props.collapsed.columns.slice(), categories.value.slice()],
  updateAllIndeterminateStates,
  { immediate: true },
)
</script>
