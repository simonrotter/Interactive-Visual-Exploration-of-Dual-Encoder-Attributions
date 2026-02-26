<template>
  <div ref="chartContainer" class="chart-container">
    <svg ref="svg" :height="height"></svg>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import { getPOSDisplayName } from '../js/posUtils.js'

const props = defineProps({
  attributionModel: Object,
  collapsed: Object,
})

const emit = defineEmits(['update:highlight', 'update:collapsed'])

const svg = ref(null)
const chartContainer = ref(null)
const height = 450
const width = ref(600)
const isLightMode = window.matchMedia('(prefers-color-scheme: light)').matches

let resizeObserver = null

function buildCategoryIndexMap(model) {
  const aCats = model.tokens_a_categorized || []
  const bCats = model.tokens_b_categorized || []

  const map = {}
  aCats.forEach((cat, i) => {
    if (!map[cat]) map[cat] = { aIndices: new Set(), bIndices: new Set() }
    map[cat].aIndices.add(i)
  })
  bCats.forEach((cat, i) => {
    if (!map[cat]) map[cat] = { aIndices: new Set(), bIndices: new Set() }
    map[cat].bIndices.add(i)
  })
  return map
}

function isCollapsed(cat, map, collapsed) {
  const entry = map[cat]
  if (!entry) return 'visible'

  const { aIndices, bIndices } = entry
  const rows = new Set(collapsed?.rows || [])
  const columns = new Set(collapsed?.columns || [])

  const aHidden = [...aIndices].filter((i) => rows.has(i)).length
  const bHidden = [...bIndices].filter((i) => columns.has(i)).length
  const aTotal = aIndices.size
  const bTotal = bIndices.size

  if (aHidden === aTotal && bHidden === bTotal) return 'collapsed'
  if (aHidden > 0 || bHidden > 0) return 'partial'
  return 'visible'
}

function computeAttributionPerCategory(model, collapsed) {
  const { tokens_a_categorized = [], tokens_b_categorized = [], attributions = [] } = model || {}
  const posSums = {}

  const allPOS = Array.from(new Set([...tokens_a_categorized, ...tokens_b_categorized]))
  allPOS.forEach((pos) => {
    posSums[pos] = 0
  })

  for (let i = 0; i < tokens_a_categorized.length; i++) {
    const pos = tokens_a_categorized[i]
    const sum = attributions[i]?.reduce((acc, val) => acc + val, 0) || 0
    posSums[pos] += sum
  }

  for (let j = 0; j < tokens_b_categorized.length; j++) {
    const pos = tokens_b_categorized[j]
    let sum = 0
    for (let i = 0; i < attributions.length; i++) {
      sum += attributions[i]?.[j] || 0
    }
    posSums[pos] += sum
  }

  const map = buildCategoryIndexMap(model)

  return Object.entries(posSums).map(([pos, value]) => ({
    pos,
    label: getPOSDisplayName(pos),
    value,
    collapseState: isCollapsed(pos, map, collapsed),
  }))
}

function renderChart(data) {
  if (!svg.value) return

  const svgEl = d3.select(svg.value)
  svgEl.selectAll('*').remove()

  const margin = { top: 20, right: 20, bottom: 90, left: 60 }
  const innerWidth = width.value - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom

  const x = d3
    .scaleBand()
    .domain(data.map((d) => d.label))
    .range([0, innerWidth])
    .padding(0.2)

  const maxValue = d3.max(data, (d) => Math.abs(d.value))
  const epsilon = 1e-6 //prevent 0

  const y = d3
    .scaleLog()
    .domain([epsilon, maxValue]) //start from epsilon
    .range([innerHeight, 0])
    .nice()

  const g = svgEl
    .attr('width', width.value)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
  const logTicks = y.ticks().filter(
    (t) => Number.isInteger(Math.log10(t)), //keep only exact powers of 10 as ticks on yaxis
  )

  g.append('g').call(d3.axisLeft(y).tickValues(logTicks).tickFormat(d3.format(',')))

  g.append('g')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')

  g.selectAll('.bar')
    .data(data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d) => x(d.label))
    .attr('y', (d) => y(Math.max(Math.abs(d.value), epsilon)))
    .attr('height', (d) => y(epsilon) - y(Math.max(Math.abs(d.value), epsilon)))
    .attr('width', x.bandwidth())
    .attr('fill', (d) => {
      const isPositive = d.value >= 0
      const color = isPositive ? '#e74c3c' : '#3a72cd'

      if (d.collapseState === 'collapsed') {
        if (isLightMode) {
          return isPositive ? '#f4c6c6' : '#c6d5f4'
        } else {
          return isPositive ? '#7e0000' : '#1c3866'
        }
      }

      if (d.collapseState === 'partial') {
        return `url(#${isPositive ? 'redHatch' : 'blueHatch'})`
      }

      return color
    })

    .on('mouseover', function (event, d) {
      emit('update:highlight', d.pos)

      d3.select(svg.value)
        .selectAll('.bar')
        .style('opacity', (b) => (b.pos === d.pos ? 1 : 0.4))
    })
    .on('mouseout', function () {
      emit('update:highlight', '')
      d3.select(svg.value).selectAll('.bar').style('opacity', 1)
    })
    .on('click', function (event, d) {
      event.stopPropagation()
      const map = buildCategoryIndexMap(props.attributionModel)
      const entry = map[d.pos]
      if (!entry) return

      //Clone existing collapsed sets
      const rowsSet = new Set(props.collapsed?.rows || [])
      const colsSet = new Set(props.collapsed?.columns || [])

      if (d.collapseState === 'visible') {
        //collapse
        entry.aIndices.forEach((i) => rowsSet.add(i))
        entry.bIndices.forEach((i) => colsSet.add(i))
      } else {
        //expand
        entry.aIndices.forEach((i) => rowsSet.delete(i))
        entry.bIndices.forEach((i) => colsSet.delete(i))
      }

      emit('update:collapsed', {
        rows: Array.from(rowsSet),
        columns: Array.from(colsSet),
      })
    })

  svgEl.select('defs').remove() //clear old patterns

  const defs = svgEl.append('defs')

  //Blue hatch
  defs
    .append('pattern')
    .attr('id', 'blueHatch')
    .attr('patternUnits', 'userSpaceOnUse')
    .attr('width', 8)
    .attr('height', 8)
    .append('path')
    .attr('d', 'M-2,2 l8,-8 M0,8 l8,-8 M6,10 l8,-8')
    .attr('stroke', '#3a72cd')
    .attr('stroke-width', 2)

  //Red  hatch
  defs
    .append('pattern')
    .attr('id', 'redHatch')
    .attr('patternUnits', 'userSpaceOnUse')
    .attr('width', 8)
    .attr('height', 8)
    .append('path')
    .attr('d', 'M-2,2 l8,-8 M0,8 l8,-8 M6,10 l8,-8')
    .attr('stroke', '#e74c3c')
    .attr('stroke-width', 2)
}

function updateChart() {
  if (!props.attributionModel) return
  const data = computeAttributionPerCategory(props.attributionModel, props.collapsed)
  renderChart(data)
}

function updateWidthAndRender() {
  if (chartContainer.value) {
    width.value = chartContainer.value.clientWidth
    updateChart()
  }
}

onMounted(() => {
  updateWidthAndRender()
  resizeObserver = new ResizeObserver(updateWidthAndRender)
  resizeObserver.observe(chartContainer.value)
})

onBeforeUnmount(() => {
  if (resizeObserver && chartContainer.value) {
    resizeObserver.unobserve(chartContainer.value)
  }
})

watch(
  () => [props.attributionModel, props.collapsed],
  () => {
    updateWidthAndRender()
  },
  { immediate: true, deep: true },
)
</script>

<style scoped>
.chart-container {
  width: 100%;
}
.bar {
  transition:
    height 0.3s,
    y 0.3s;
}
</style>
