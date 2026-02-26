<template>
  <div style="display: grid; align-self: flex-start">
    <div style="display: flex; height: 24px">
      <PercentageBar
        color="#b5853c"
        :value="selectionShare"
        customText="Attributions:"
        class="mr-2 ml-2"
      />
      <LeftRightBar
        :value="selectionSumScaled"
        customText="Sum:"
        :display-value="selectionSum"
        class="mr-2 ml-2"
      />
    </div>
    <div style="display: flex; align-self: flex-start; position: relative">
      <!-- Left Handle -->
      <div
        ref="leftSliderBtn"
        class="sliderButton"
        @mousedown="startLeftSliding"
        :style="{
          left: '-5px',
          cursor: isSlidingLeft ? 'none' : 'ew-resize',
          backgroundColor: isSlidingLeft ? '#32a852' : '',
          position: 'absolute',
        }"
      ></div>

      <div ref="histogramChart"></div>

      <!-- Right Hande -->
      <div
        ref="rightSliderBtn"
        class="sliderButton"
        @mousedown="startRightSliding"
        :style="{
          right: '-7px',
          cursor: isSlidingRight ? 'none' : 'ew-resize',
          backgroundColor: isSlidingRight ? '#32a852' : '',
          position: 'absolute',
        }"
      ></div>
    </div>
    <FancySlider
      v-model="sliderPosition"
      :min="0"
      :max="zoomSliderResolution"
      @input="zoomToData"
      :text="autoZoomText"
      :color="isManualZoom ? '#6e6e6e' : null"
      class="mb-4 w-full h-[24px]"
    />
    <div style="display: flex">
      <div style="display: grid">
        <button
          class="py-1.5 px-3 m-1 text-white bg-[#b81e1e] border-none rounded cursor-pointer"
          @click="((histogramLeftvalue = 0), (histogramRightvalue = 1))"
        >
          all +
        </button>
        <button
          class="py-1.5 px-3 m-1 text-white bg-[#1e2db8] border-none rounded cursor-pointer"
          @click="((histogramLeftvalue = -1), (histogramRightvalue = 0))"
        >
          all -
        </button>
      </div>
      <div v-if="isZoomedIn">
        <button
          @click="resetZoom"
          class="py-1.5 px-3 m-1 bg-neutral-300 dark:bg-neutral-700 border-none rounded cursor-pointer"
        >
          Reset Zoom
        </button>
      </div>
      <div>
        <button
          v-if="rightClickBrushBounds != null"
          @click="resetRightClickBrush"
          class="py-1.5 px-3 m-1 bg-neutral-300 dark:bg-neutral-700 border-none rounded cursor-pointer"
        >
          Reset negative Selection
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { getAttributionShare } from '../js/utils'
import PercentageBar from '@/components/PercentageBar.vue'
import LeftRightBar from './LeftRightBar.vue'
import * as d3 from 'd3'
import FancySlider from './FancySlider.vue'

const props = defineProps({
  histogramData: {
    type: Array,
    required: true,
  },
})

const isManualZoom = ref(false)

function flattenHistogramData(data) {
  //Handle 2D or 3D arrays
  if (!Array.isArray(data)) return []
  if (typeof data[0]?.[0] === 'number') {
    //2D array: flatten once
    return data.flat()
  } else if (Array.isArray(data[0]?.[0])) {
    //3D array: flatten twice
    return data.flat(2)
  }
  return []
}

const emit = defineEmits(['range-changed', 'negative-range-changed', 'range-handle-active'])
const histogramChart = ref(null)
//bounds
const histogramLeftvalue = ref(-1)
const histogramRightvalue = ref(1)

//array of negative selection bounds
const rightClickBrushBounds = ref(null)

//holds x axis scaling, which is updated on zoom
const currentXScale = ref(null)

//check which sliderhandle is used
const isSlidingLeft = ref(false)
const isSlidingRight = ref(false)

const shouldAnimate = ref(true)

//constant number of bins (bars) in the histogram / zoom causes re-render
const binsCount = 150

const histogramWidth = 500
const histogramHeight = 300
const histogramMargin = { top: 20, right: 10, bottom: 30, left: 30 }

//step count for auto-zoom slider
const zoomSliderResolution = 1000

const xOrig = d3
  .scaleSymlog()
  .domain([-1, 1])
  .range([histogramMargin.left, histogramWidth - histogramMargin.right])
  .constant(0.2)

currentXScale.value = xOrig

//initially set to 100%
const sliderPosition = ref(zoomSliderResolution)

const selectionShare = ref(1)
const selectionSum = ref(0)
const selectionSumScaled = ref(0)

const visibleDataPercent = computed(() => {
  const flatData = flattenHistogramData(props.histogramData)
  if (!flatData.length) return 100
  const left = histogramLeftvalue.value
  const right = histogramRightvalue.value
  const visibleCount = flatData.filter((v) => v >= left && v <= right).length
  return Math.round((visibleCount / flatData.length) * 1000) / 10 // one decimal place
})

const autoZoomText = computed(() => {
  return `Visible Data: ${visibleDataPercent.value}%`
})

const isZoomedIn = computed(() => {
  return histogramLeftvalue.value > -1 || histogramRightvalue.value < 1
})

function resetZoom() {
  isManualZoom.value = true
  histogramLeftvalue.value = -1
  histogramRightvalue.value = 1
}

function getAdaptiveColorScale(left, right) {
  const maxAbs = Math.max(Math.abs(left), Math.abs(right), 0.00001) //avoid zero
  return d3
    .scaleLinear()
    .domain([-maxAbs, 0, maxAbs])
    .range(['#3b82f6', '#e5e7eb', '#ef4444'])
    .interpolate(d3.interpolateLab)
    .clamp(true)
}

//move the negative brush according to a new x axis, so after zoomin it stays at its x axis bounds
const updateRightClickBrush = (xNew) => {
  if (!rightClickBrushBounds.value) return

  const [x0, x1] = rightClickBrushBounds.value
  const x0Scaled = xNew(x0)
  const x1Scaled = xNew(x1)

  const brushLayer = d3
    .select(histogramChart.value)
    .select('.zoom-group')
    .select('.right-click-brush-layer')

  const existing = brushLayer.selectAll('rect')

  if (existing.empty()) {
    //Create new brush rect if not present
    brushLayer
      .append('rect')
      .attr('x', Math.min(x0Scaled, x1Scaled))
      .attr('y', histogramMargin.top)
      .attr('width', Math.abs(x1Scaled - x0Scaled))
      .attr('height', histogramHeight - histogramMargin.top - histogramMargin.bottom)
      .attr('fill', 'rgba(255, 0, 0, 0.3)')
      .attr('stroke', 'red')
      .attr('stroke-width', 1)
  } else {
    //check if button is used (animate) or dragging slider (dont animate)
    if (shouldAnimate.value) {
      existing
        .transition()
        .duration(300)
        .attr('x', Math.min(x0Scaled, x1Scaled))
        .attr('width', Math.abs(x1Scaled - x0Scaled))
    } else {
      existing.attr('x', Math.min(x0Scaled, x1Scaled)).attr('width', Math.abs(x1Scaled - x0Scaled))
    }
  }
}

//automatically update histogram when prop is changing
watch(
  () => props.histogramData,
  (newData) => {
    if (newData && newData.length > 0) {
      drawHistogram()
      zoomToData(1) //zoom to 100% of the data toactually show it else most data is at 0
      applyZoom()
    }
  },
  { immediate: true },
)

watch([() => isSlidingLeft.value, () => isSlidingRight.value], () => {
  emit('range-handle-active', isSlidingLeft.value || isSlidingRight.value)
})

//main function for creation of histogram
//creates or replaces existing histogram
function drawHistogram() {
  const data = flattenHistogramData(props.histogramData)
  let svg = d3.select(histogramChart.value).select('svg')

  //check if old histogram exists
  if (!svg.empty()) {
    svg.selectAll('*').remove()
  } else {
    svg = d3
      .select(histogramChart.value)
      .append('svg')
      .attr('width', histogramWidth)
      .attr('height', histogramHeight)
  }

  //plot data into bins
  const binGenerator = d3.bin().domain([-1, 1]).thresholds(binsCount)
  const bins = binGenerator(data)
  const maxCount = Math.max(1, d3.max(bins, (d) => d.length) || 1)
  const y = d3
    .scaleSymlog()
    .constant(1) //workaround fro log hiding 0
    .domain([0, maxCount])
    .range([histogramHeight - histogramMargin.bottom, histogramMargin.top])
  //blue-white-red color scale
  const colorScale = getAdaptiveColorScale(histogramLeftvalue.value, histogramRightvalue.value)

  //clip pth to prevent spill over axis
  svg
    .append('defs')
    .append('clipPath')
    .attr('id', 'chart-area-clip')
    .append('rect')
    .attr('x', histogramMargin.left)
    .attr('y', histogramMargin.top)
    .attr('width', histogramWidth - histogramMargin.left - histogramMargin.right)
    .attr('height', histogramHeight - histogramMargin.top - histogramMargin.bottom)

  const zoomGroup = svg
    .append('g')
    .attr('class', 'zoom-group')
    .attr('clip-path', 'url(#chart-area-clip)')

  //add bins to clipped container
  zoomGroup
    .append('g')
    .selectAll('rect')
    .data(bins)
    .join('rect')
    .attr('class', 'bar')
    .attr('x', (d) => xOrig(d.x0))
    .attr('y', (d) => y(d.length))
    .attr('width', (d) => xOrig(d.x1) - xOrig(d.x0))
    .attr('height', (d) => y(0) - y(d.length))
    .attr('fill', (d) => {
      const avg = d3.mean(d)
      return avg != null ? colorScale(avg) : '#ccc'
    })

  //x and y axis are separate to be omitted from clipping
  svg
    .append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0,${histogramHeight - histogramMargin.bottom})`)
    .call(d3.axisBottom(xOrig))

  svg
    .append('g')
    .attr('class', 'y-axis')
    .attr('transform', `translate(${histogramMargin.left},0)`)
    .call(
      d3
        .axisLeft(y)
        .ticks(20)
        .tickFormat((d) => {
          if (d === 0) return '0'

          const log10 = Math.log10(d)

          //show ticks if its a power of 10
          if (Number.isInteger(log10)) return d3.format(',')(d)

          //if its  5 × 10^n
          const log10Div = Math.log10(d / 5)
          if (Number.isInteger(log10Div)) return d3.format(',')(d)

          return ''
        }),
    )

  //add the brush for zooming (doesnt need to be in zoomgroup as it instantly gets removed on selection)
  const brush = d3
    .brushX()
    .extent([
      [histogramMargin.left, histogramMargin.top],
      [histogramWidth - histogramMargin.right, histogramHeight - histogramMargin.bottom],
    ])
    .on('end', brushed)

  svg
    .append('g')
    .attr('class', 'brush')
    .call(brush)
    .select('.selection')
    .attr('fill', 'rgba(0, 255, 125, 0.5)')
    .attr('stroke', 'green')

  let rightBrushGroup = zoomGroup.append('g').attr('class', 'right-click-brush-layer')

  let isRightDragging = false
  let dragStartX = null

  //Prevent context menu for the rict lick dragging window
  svg.on('contextmenu', (event) => {
    event.preventDefault()
  })

  //mouse listeners for right click brush
  //initialize with right click
  svg.on('mousedown', (event) => {
    if (event.button !== 2) return

    //prevent a click to propagate down and potetntionally count as a selection click in another component (here it would cause a null selection in the textChart causing a selectio nreset)
    event.preventDefault()

    isRightDragging = true
    dragStartX = d3.pointer(event)[0]

    //remove old rightclick brush
    rightBrushGroup.selectAll('*').remove()
  })

  //collect distance and draw brush
  svg.on('mousemove', (event) => {
    if (!isRightDragging) return

    const [x] = d3.pointer(event)
    const x0 = Math.min(dragStartX, x)
    const x1 = Math.max(dragStartX, x)

    rightBrushGroup.selectAll('rect').remove()

    rightBrushGroup
      .append('rect')
      .attr('x', x0)
      .attr('y', histogramMargin.top)
      .attr('width', x1 - x0)
      .attr('height', histogramHeight - histogramMargin.top - histogramMargin.bottom)
      .attr('fill', 'rgba(255, 0, 0, 0.3)')
      .attr('stroke', 'red')
      .attr('stroke-width', 1)
  })

  //store selected values (x scale is inverted)
  svg.on('mouseup', (event) => {
    if (!isRightDragging) return
    isRightDragging = false

    const [x] = d3.pointer(event)
    const x0 = Math.min(dragStartX, x)
    const x1 = Math.max(dragStartX, x)

    const xScale = currentXScale.value

    const x0Value = xScale.invert(x0)
    const x1Value = xScale.invert(x1)

    rightClickBrushBounds.value = [x0Value, x1Value]
    const left = x0Value
    const right = x1Value
    emit('negative-range-changed', { left, right })
    const attributionShareModel = getAttributionShare(
      props.histogramData,
      { left: histogramLeftvalue.value, right: histogramRightvalue.value },
      { left, right },
    )
    selectionShare.value = attributionShareModel.massShare
    selectionSumScaled.value = attributionShareModel.signedShare
    selectionSum.value = attributionShareModel.signedSum
  })
}

//handler for normal left click zoom brush
function brushed(event) {
  if (event.selection) {
    const xSubset = d3
      .scaleSymlog()
      .domain([histogramLeftvalue.value, histogramRightvalue.value])
      .range([histogramMargin.left, histogramWidth - histogramMargin.right])
      .constant(0.2)
    const [x0, x1] = event.selection.map(xSubset.invert)

    histogramLeftvalue.value = x0
    histogramRightvalue.value = x1

    isManualZoom.value = true

    //reset brush for new selection by removing and recreating
    d3.select(histogramChart.value).select('.brush').remove()
    const brush = d3
      .brushX()
      .extent([
        [histogramMargin.left, histogramMargin.top],
        [histogramWidth - histogramMargin.right, histogramHeight - histogramMargin.bottom],
      ])
      .on('end', brushed)

    d3.select(histogramChart.value)
      .select('svg')
      .append('g')
      .attr('class', 'brush')
      .call(brush)
      .select('.selection')
      .attr('fill', 'rgba(0, 255, 125, 0.5)')
      .attr('stroke', 'green')
  }
}

//function that handles redrawing of histogram when bounds changed (zooming)
function applyZoom() {
  const left = histogramLeftvalue.value
  const right = histogramRightvalue.value

  const xNew = d3
    .scaleSymlog()
    .domain([left, right])
    .range([histogramMargin.left, histogramWidth - histogramMargin.right])
    .constant(0.2)
  currentXScale.value = xNew

  //if trigger comes from a button click or anything else, animate the change
  if (shouldAnimate.value) {
    d3.select(histogramChart.value)
      .select('.x-axis')
      .transition()
      .duration(300)
      .call(d3.axisBottom(xNew))

    const bars = d3.select(histogramChart.value).select('.zoom-group').selectAll('rect.bar')

    let transitionEndCount = 0
    const totalBars = bars.size()

    bars
      .transition()
      .duration(300)
      .attr('x', (d) => xNew(d.x0))
      .attr('width', (d) => xNew(d.x1) - xNew(d.x0))
      .on('end', () => {
        transitionEndCount++
        if (transitionEndCount === totalBars) {
          //update the bins after all transitions have completed
          updateBins(left, right, xNew)
        }
      })
  } else {
    //update the x-axis/bars immediately without animation when trigger comes from drag slider
    //this prevenents sluggish feeling
    d3.select(histogramChart.value).select('.x-axis').call(d3.axisBottom(xNew))
    const bars = d3.select(histogramChart.value).select('.zoom-group').selectAll('rect.bar')

    bars.attr('x', (d) => xNew(d.x0)).attr('width', (d) => xNew(d.x1) - xNew(d.x0))
    updateBins(left, right, xNew)
  }
  //trigger redrawing of the negative selection so that it still matches the changed x axis
  updateRightClickBrush(xNew)
}

//deletes negative brush
function resetRightClickBrush() {
  const svg = d3.select(histogramChart.value).select('svg')

  svg.select('.zoom-group').select('.right-click-brush-layer').selectAll('rect').remove()

  rightClickBrushBounds.value = null
  const left = 0
  const right = 0
  emit('negative-range-changed', { left, right })
  const attributionShareModel = getAttributionShare(
    props.histogramData,
    { left: histogramLeftvalue.value, right: histogramRightvalue.value },
    { left, right },
  )
  selectionShare.value = attributionShareModel.massShare
  selectionSumScaled.value = attributionShareModel.signedShare
  selectionSum.value = attributionShareModel.signedSum
}

//to also zoom in with high resolution redraw the bins after every zoom, to again have the set bin count
function updateBins(left, right, xNew) {
  const binGenerator = d3.bin().domain([left, right]).thresholds(binsCount)
  const data = flattenHistogramData(props.histogramData)
  const bins = binGenerator(data)

  const maxCount = Math.max(1, d3.max(bins, (d) => d.length) || 1)
  const y = d3
    .scaleSymlog()
    .constant(1)
    .domain([0, maxCount])
    .range([histogramHeight - histogramMargin.bottom, histogramMargin.top])

  const colorScale = getAdaptiveColorScale(left, right)

  //update the y-axis to match the new bin height
  d3.select(histogramChart.value)
    .select('.y-axis')
    .call(d3.axisLeft(y))
    .attr('transform', `translate(${histogramMargin.left},0)`)
    .call(
      d3
        .axisLeft(y)
        .ticks(20)
        .tickFormat((d) => {
          if (d === 0) return '0'

          const log10 = Math.log10(d)

          //ticks like before
          if (Number.isInteger(log10)) return d3.format(',')(d)
          const log10Div = Math.log10(d / 5)
          if (Number.isInteger(log10Div)) return d3.format(',')(d)

          return ''
        }),
    )

  const zoomGroup = d3.select(histogramChart.value).select('.zoom-group')

  //select only the bars inside that group and update to new zoom level
  zoomGroup
    .selectAll('rect.bar')
    .data(bins)
    .join('rect')
    .attr('class', 'bar')
    .attr('x', (d) => xNew(d.x0))
    .attr('width', (d) => xNew(d.x1) - xNew(d.x0))
    .attr('y', (d) => y(d.length))
    .attr('height', (d) => y(0) - y(d.length))
    .attr('fill', (d) => {
      const avg = d3.mean(d)
      return avg != null ? colorScale(avg) : '#ccc'
    })

  emit('range-changed', { left, right })
  let negativeBounds = rightClickBrushBounds.value
  if (!negativeBounds) {
    negativeBounds = [0, 0]
  }
  const attributionShareModel = getAttributionShare(
    props.histogramData,
    { left, right },
    { left: negativeBounds[0], right: negativeBounds[1] },
  )
  selectionShare.value = attributionShareModel.massShare
  selectionSumScaled.value = attributionShareModel.signedShare
  selectionSum.value = attributionShareModel.signedSum
}

//capture any change in bounds and start triggering of all redrawing with the applyZoom function
watch([histogramLeftvalue, histogramRightvalue], applyZoom)

//LEFT drag slider
function startLeftSliding(event) {
  isSlidingLeft.value = true
  initMouseSlider(event, 'left')
}

//RIGHT slider
function startRightSliding(event) {
  isSlidingRight.value = true
  initMouseSlider(event, 'right')
}

//function to capture mouse dragging for sliders, mouse is hidden while sliding. there is the option to lock the mouse and hide, to allow infinite sliding and prevent hover efefects, but that doesnt work on safari.
//so this is the workaround hiding the mouse and measurin x movement. but has disadv: mouse can only move on screen space . hoer effect like when mouse goes over matrix or pos charts,are prevented by showing an invisible overlay during sldiing
function initMouseSlider(event, side) {
  shouldAnimate.value = false
  let lastClientX = event.clientX

  //hide mouse
  document.body.style.cursor = 'none'
  document.body.style.userSelect = 'none'

  //add overlay to prevent hover ffects
  const overlay = document.createElement('div')
  Object.assign(overlay.style, {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    cursor: 'none',
    zIndex: 999999, //above everything
  })
  document.body.appendChild(overlay)

  //remove brushing durin sliding to prevent cursor to reappear because d3 brushing always wants to display crosshair
  d3.select(histogramChart.value).select('.brush').remove()

  function onMouseMove(e) {
    const deltaPx = e.clientX - lastClientX
    lastClientX = e.clientX

    isManualZoom.value = true

    //dynamic scale based on the current zoom level, so that scrolling feels natural and linear
    const xScale = d3
      .scaleSymlog()
      .domain([histogramLeftvalue.value, histogramRightvalue.value])
      .range([histogramMargin.left, histogramWidth - histogramMargin.right])
      .constant(0.2)
    const currentValue = side === 'right' ? histogramRightvalue.value : histogramLeftvalue.value
    const currentPx = xScale(currentValue)

    const newPx = currentPx + deltaPx
    let newDomainValue = xScale.invert(newPx)

    //prevent infinite zoom and negative space between bounds
    if (side === 'right') {
      histogramRightvalue.value = Math.min(
        1,
        Math.max(histogramLeftvalue.value + 0.00001, newDomainValue),
      )
    } else {
      histogramLeftvalue.value = Math.max(
        -1,
        Math.min(histogramRightvalue.value - 0.00001, newDomainValue),
      )
    }
  }

  //end of sliding operations
  function stopSliding() {
    isSlidingLeft.value = false
    isSlidingRight.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    overlay.remove()
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', stopSliding)
    shouldAnimate.value = true //re enable animations for zooming
    //re enable brush
    const brush = d3
      .brushX()
      .extent([
        [histogramMargin.left, histogramMargin.top],
        [histogramWidth - histogramMargin.right, histogramHeight - histogramMargin.bottom],
      ])
      .on('end', brushed)

    d3.select(histogramChart.value)
      .select('svg')
      .append('g')
      .attr('class', 'brush')
      .call(brush)
      .select('.selection')
      .attr('fill', 'rgba(0, 255, 125, 0.5)')
      .attr('stroke', 'green')
  }

  //hook mouse listeners
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopSliding)
}

//finds and zooms to the range where the included bins represent the given percentage of the whole data
function zoomToData(zoomPercent = 1) {
  const flatData = flattenHistogramData(props.histogramData)
  const minDomain = -1
  const maxDomain = 1
  isManualZoom.value = false

  if (!flatData.length || zoomPercent <= 0 || zoomPercent > 1) {
    histogramLeftvalue.value = minDomain
    histogramRightvalue.value = maxDomain
    return
  }

  const sorted = flatData.slice().sort((a, b) => a - b)

  const total = sorted.length
  const targetCount = Math.floor(total * zoomPercent)

  //Try to find the tightest window centered around 0 that contains the targetCount points
  let bestRange = { min: minDomain, max: maxDomain, score: Infinity }

  for (let i = 0; i <= total - targetCount; i++) {
    const subrange = sorted.slice(i, i + targetCount)
    const rangeMin = subrange[0]
    const rangeMax = subrange[subrange.length - 1]

    //Compute how centered it is around 0
    const centerOffset = Math.abs((rangeMax + rangeMin) / 2)
    const width = rangeMax - rangeMin

    //Prefer ranges that are more centered and narrower
    const score = centerOffset + width * 0.1

    if (score < bestRange.score) {
      bestRange = { min: rangeMin, max: rangeMax, score }
    }
  }

  //Clamp to domain
  histogramLeftvalue.value = Math.max(bestRange.min, minDomain)
  histogramRightvalue.value = Math.min(bestRange.max, maxDomain)
}

onMounted(() => {
  drawHistogram()
})
</script>

<style scoped>
.sliderButton {
  @apply cursor-ew-resize border-none rounded-[5px] w-[5px] mt-5 mb-[30px] h-[260px] bg-neutral-300 dark:bg-[#494949];
}
.sliderButton:hover {
  background-color: #32a852;
}
</style>
