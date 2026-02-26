<template>
  <div>
    <div
      id="matrix-tooltip"
      style="
        position: absolute;
        pointer-events: none;
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(20px) contrast(60%);
        color: white;
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
        display: none;
      "
    ></div>

    <div style="display: flex">
      <div ref="chart"></div>
      <div
        style="width: 450px; height: 100%"
        class="bg-neutral-200 dark:bg-neutral-700 p-2 rounded-[15px] ml-10 mb-3"
      >
        <div style="display: flex; align-items: center; margin: 0.25rem">
          <FancySlider
            v-model="collapseThresholdPosition"
            :min="0"
            :max="1"
            @input="collapseLowAttributionRowsAndColumns()"
            :text="collapseThresholdText"
            style="width: 100%; height: 36px"
            :step="0.001"
            :color="attributionSliderColor"
          />
          <MultitextToggle
            v-model="collapseThresholdMode"
            :labels="['+/-', '+', '-']"
            class="ml-2"
          />
        </div>
        <div
          @mousedown.stop
          @mouseup.stop
          @click.stop
          v-if="attributionModel.tokens_a_categorized || attributionModel.tokens_b_categorized"
        >
          <PosSelector
            :attributionModel="attributionModel"
            :collapsed="collapsed"
            @update:collapsed="updateCollapsed"
            class="mt-4"
          />
          <PosChart
            :attributionModel="attributionModel"
            :collapsed="collapsed"
            class="mt-4"
            @update:highlight="updateHighlight"
            @update:collapsed="updateCollapsed"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'

import * as d3 from 'd3'
import FancySlider from './FancySlider.vue'
import PosSelector from './PosSelector.vue'
import { arraysEqual } from '../js/utils.js'
import MultitextToggle from '@/components/MultitextToggle.vue'
import PosChart from './PosChart.vue'
import { getPOSDisplayName } from '../js/posUtils.js'

export default {
  name: 'Chart2D',
  components: {
    FancySlider,
    PosSelector,
    MultitextToggle,
    PosChart,
  },
  props: {
    attributionModel: {
      type: Object,
      required: true,
    },
    bounds: {
      type: Object,
      required: true,
    },
    negativeBounds: {
      type: Object,
      required: true,
    },
    selection: {
      type: Object,
      required: true,
    },
  },
  setup(props, { emit }) {
    const chart = ref()
    const selectedTokens = ref({ tokens_a: [], tokens_b: [] })

    const chartMargin = { top: 0, right: 0, bottom: 60, left: 90 }
    const chartWidth = 550 - chartMargin.left - chartMargin.right
    const chartHeight = 550 - chartMargin.top - chartMargin.bottom

    const highlightedPOSTag = ref()

    const collapsed = ref({
      rows: [],
      columns: [],
    })

    const isLightMode = window.matchMedia('(prefers-color-scheme: light)').matches

    const attributionSliderColor = ref()

    const collapseThresholdMode = ref(0)

    const collapseThresholdText = computed(() => {
      return `Threshold for Collapsing: < ${Math.round(collapseThreshold.value * 1000) / 1000}`
    })

    const collapseThreshold = computed(() => {
      return Math.pow(collapseThresholdPosition.value, 3)
    })

    function computeQuantile(attributions, q = 0.8) {
      if (!attributions || !attributions.length) return 0.025 //fallback, should not be used
      const flatValues = attributions
        .flat()
        .map(Math.abs)
        .sort((a, b) => a - b)
      const pos = Math.floor(q * (flatValues.length - 1))
      return flatValues[pos]
    }

    const quantile = computeQuantile(props.attributionModel?.attributions)
    const collapseThresholdPosition = ref(Math.pow(quantile, 1 / 3))

    function filterAttributionModel() {
      let filtered = { ...props.attributionModel }

      filtered.selectedAttributions = props.attributionModel.attributions?.map((row) =>
        row.map((value) => (value < props.bounds?.left || value > props.bounds?.right ? 0 : value)),
      )

      filtered.unselectedAttributions = props.attributionModel.attributions?.map((row) =>
        row.map((value) => (value < props.bounds?.left || value > props.bounds?.right ? value : 0)),
      )

      filtered.excludedAttributions = props.attributionModel.attributions?.map((row) =>
        row.map((value) =>
          value > props.negativeBounds?.left && value < props.negativeBounds?.right ? value : 0,
        ),
      )
      return filtered
    }

    //calalates the whole positions of matrix elements
    function getAdjustedScales() {
      const tokens_a = props.attributionModel.tokens_a
      const tokens_b = props.attributionModel.tokens_b

      const collapseSize = 6

      //compute widths of columns (normal or collapsed)
      const columnWidths = (tokens_b ?? []).map((_, j) =>
        collapsed.value.columns.includes(j)
          ? collapseSize
          : (chartWidth - collapseSize * collapsed.value.columns.length) /
            (tokens_b.length - collapsed.value.columns.length),
      )

      //compute heights of rows
      const rowHeights = (tokens_a ?? []).map((_, i) =>
        collapsed.value.rows.includes(props.attributionModel.tokens_a?.length - i - 1)
          ? collapseSize
          : (chartHeight - collapseSize * collapsed.value.rows.length) /
            (tokens_a.length - collapsed.value.rows.length),
      )

      //new positions of collumns
      const xPositions = []
      let cumX = 0
      for (let j = 0; j < tokens_b?.length; j++) {
        xPositions.push(cumX)
        cumX += columnWidths[j]
      }

      //positions comulation of rows
      const yPositions = []
      let cumY = 0
      for (let i = tokens_a?.length - 1; i >= 0; i--) {
        //a is reveresd, keep
        yPositions[i] = cumY
        cumY += rowHeights[i]
      }

      //map indices to positions
      const xScale = (index) => xPositions[index]
      xScale.bandwidth = () => 0
      xScale.bandwidthAt = (index) => columnWidths[index]

      const yScale = (index) => yPositions[index]
      yScale.bandwidth = () => 0
      yScale.bandwidthAt = (index) => rowHeights[index]

      return { xScale, yScale }
    }

    function highlightOpacity(d) {
      if (!highlightedPOSTag.value) return 1 //early exit default nothing highlight

      const posA =
        props.attributionModel.tokens_a_categorized?.[
          props.attributionModel.tokens_a.length - 1 - d.i
        ]
      const posB = props.attributionModel.tokens_b_categorized?.[d.j]

      const isHighlighted = posA === highlightedPOSTag.value || posB === highlightedPOSTag.value

      if (isHighlighted) return 1 //is in highligt group
      if (isLightMode) return 'dim' //light mode
      return 0.6 //dark mode
    }

    const createChart = () => {
      const tokens_a = props.attributionModel.tokens_a?.slice().reverse()
      const tokens_b = props.attributionModel.tokens_b
      const filtered = filterAttributionModel()

      const prepareData = (attributions) => {
        const data = []
        tokens_a?.forEach((tokenA, i) => {
          tokens_b?.forEach((tokenB, j) => {
            const raw = attributions[tokens_a.length - 1 - i][j]
            const val = Math.sign(raw) * Math.sqrt(Math.abs(raw))
            data.push({ i, j, x: tokenB, y: tokenA, value: val })
          })
        })
        return data
      }

      let svg = d3.select(chart.value).select('svg')

      if (!svg.empty()) {
        svg.selectAll('*').remove()
      } else {
        svg = d3
          .select(chart.value)
          .append('svg')
          .attr('width', chartWidth + chartMargin.left + chartMargin.right)
          .attr('height', chartHeight + chartMargin.top + chartMargin.bottom)
      }

      const g = svg
        .append('g')
        .attr('transform', `translate(${chartMargin.left},${chartMargin.top})`)

      const { xScale, yScale } = getAdjustedScales()

      //Axis with adjusted ticks and positions
      const xAxisScale = d3
        .scaleOrdinal()
        .domain((tokens_b ?? []).map((_, j) => j))
        .range((tokens_b ?? []).map((_, j) => xScale(j) + xScale.bandwidthAt(j) / 2))

      const yAxisScale = d3
        .scaleOrdinal()
        .domain((tokens_a ?? []).map((_, i) => i))
        .range((tokens_a ?? []).map((_, i) => yScale(i) + yScale.bandwidthAt(i) / 2))

      //show all labels, but later set opacity of collapsed 0 so its there and clickablebut hidden
      const xAxis = d3.axisBottom(xAxisScale).tickFormat((j) => tokens_b[j])

      const yAxis = d3.axisLeft(yAxisScale).tickFormat((i) => tokens_a[i])

      const xAxisG = g
        .append('g')
        .attr('transform', `translate(0,${chartHeight})`)
        .call(xAxis)
        .attr('transform', `translate(0,${chartHeight + 5})`)
        .call((g) => g.select('.domain').attr('d', `M-5,0H${chartWidth}`)) //force domain line full width shifted doesn 5px

      xAxisG
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-0.5em')
        .attr('dy', '0.15em')
        .attr('transform', 'rotate(-40)')
        .style('opacity', (j) => (collapsed.value.columns.includes(j) ? 0 : 1))
        .style('pointer-events', 'all')
        .on('mouseover', function (event, j) {
          if (collapsed.value.columns.includes(j)) {
            d3.select(this).style('opacity', 1)
          }
        })
        .on('mouseout', function (event, j) {
          if (collapsed.value.columns.includes(j)) {
            d3.select(this).style('opacity', 0)
          }
        })
        .on('click', (event, j) => {
          toggleCollapsedColumn(j)
        })

      const yAxisG = g
        .append('g')
        .call(yAxis)
        .attr('transform', `translate(-5,0)`)
        .call((g) => g.select('.domain').attr('d', `M0,0V${chartHeight + 5}`)) //force domain line full height shiften left 5px

      //opacity is 0 when its collapsed, but still 1 if hovered
      yAxisG
        .selectAll('text')
        .style('opacity', (i) =>
          collapsed.value.rows.includes(props.attributionModel.tokens_a.length - i - 1) ? 0 : 1,
        )
        .style('pointer-events', 'all')
        .on('mouseover', function (event, i) {
          const rowIndex = props.attributionModel.tokens_a.length - i - 1
          if (collapsed.value.rows.includes(rowIndex)) {
            d3.select(this).style('opacity', 1)
          }
        })
        .on('mouseout', function (event, i) {
          const rowIndex = props.attributionModel.tokens_a.length - i - 1
          if (collapsed.value.rows.includes(rowIndex)) {
            d3.select(this).style('opacity', 0)
          }
        })
        .on('click', (event, i) => {
          toggleCollapsedRow(props.attributionModel.tokens_a.length - i - 1)
        })

      const selectedData = prepareData(filtered.selectedAttributions)
      const unselectedData = prepareData(filtered.unselectedAttributions)
      const excludedData = prepareData(filtered.excludedAttributions)

      const selectedMax = d3.max(selectedData, (d) => Math.abs(d.value)) || 1
      const unselectedMax = d3.max(unselectedData, (d) => Math.abs(d.value)) || 1

      const selectedColorScale = d3
        .scaleLinear()
        .domain([-selectedMax, 0, selectedMax])
        .range(['blue', 'white', 'red'])

      const unselectedColorScale = d3
        .scaleLinear()
        .domain([-unselectedMax, 0, unselectedMax])
        .range(['blue', 'white', 'red'])

      const excludedColorScale = d3
        .scaleLinear()
        .domain([-selectedMax * 2.2, 0, selectedMax * 2.2])
        .range(['blue', 'white', 'red'])

      //Define hatching patterns once
      svg.select('defs').remove() //clear old defs
      const defs = svg.append('defs')

      defs
        .append('pattern')
        .attr('id', 'diagonalHatchWhite')
        .attr('patternUnits', 'userSpaceOnUse')
        .attr('width', 10)
        .attr('height', 10)
        .append('path')
        .attr('d', 'M0,0 l10,10')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)

      defs
        .append('pattern')
        .attr('id', 'diagonalHatchBlack')
        .attr('patternUnits', 'userSpaceOnUse')
        .attr('width', 10)
        .attr('height', 10)
        .append('path')
        .attr('d', 'M10,0 l-10,10')
        .attr('stroke', '#000')
        .attr('stroke-width', 2)
        .attr('opacity', 0.25)

      const cellMap = new Map()

      for (const d of unselectedData) {
        if (d.value !== 0) {
          const key = `${d.i},${d.j}`
          cellMap.set(key, { ...d, group: 'unselected' })
        }
      }
      for (const d of excludedData) {
        if (d.value !== 0) {
          const key = `${d.i},${d.j}`
          if (!cellMap.has(key)) {
            cellMap.set(key, { ...d, group: 'excluded' })
          }
        }
      }
      for (const d of selectedData) {
        if (d.value !== 0) {
          const key = `${d.i},${d.j}`
          if (!cellMap.has(key)) {
            cellMap.set(key, { ...d, group: 'selected' })
          }
        }
      }

      const mergedData = Array.from(cellMap.values())

      const tooltip = d3.select('#matrix-tooltip')

      const rectPadding = 2

      //position helpers
      function getX(d) {
        return xScale(d.j) + rectPadding / 2
      }
      function getY(d) {
        return yScale(d.i) + rectPadding / 2
      }
      function getWidth(d) {
        return Math.max(xScale.bandwidthAt(d.j) - rectPadding, 0)
      }
      function getHeight(d) {
        return Math.max(yScale.bandwidthAt(d.i) - rectPadding, 0)
      }

      function showTooltip(event, d) {
        const shiftHeld = event.shiftKey

        let token, posTag

        if (shiftHeld) {
          token = d.x
          posTag = props.attributionModel.tokens_b_categorized?.[d.j]
        } else {
          token = d.y
          const reversedIndex = props.attributionModel.tokens_a.length - d.i - 1
          posTag = props.attributionModel.tokens_a_categorized?.[reversedIndex]
        }

        const posName = getPOSDisplayName(posTag) || posTag || 'N/A'

        const html = `
    <div><strong>${token}</strong></div>
    <div>${d.value.toFixed(3)}</div>
    <div>${posName}</div>
  `

        tooltip.html(html).style('display', 'block')
      }

      //Selected
      g.selectAll('.data-point-selected')
        .data(mergedData.filter((d) => d.group === 'selected'))
        .enter()
        .append('rect')
        .attr('class', 'data-point-selected')
        .attr('x', getX)
        .attr('y', getY)
        .attr('width', getWidth)
        .attr('height', getHeight)
        .on('click', onClickHandler)
        .on('mouseover', function (event, d) {
          d3.select(this).classed('hovered', true)
          showTooltip(event, d)
        })
        .on('mousemove', function (event, d) {
          const shiftNow = event.shiftKey
          const tooltipEl = tooltip.node()

          //detect shift key change while hovering only on move mabye add trigger later
          if (tooltipEl._lastShift !== shiftNow) {
            tooltipEl._lastShift = shiftNow
            showTooltip(event, d)
          }

          tooltip.style('left', event.pageX + 12 + 'px').style('top', event.pageY + 12 + 'px')
        })
        .on('mouseout', function () {
          tooltip.style('display', 'none')
          tooltip.node()._lastShift = undefined
          d3.select(this).classed('hovered', false)
        })
        .style('fill', (d) => {
          const color = selectedColorScale(d.value)
          if (highlightOpacity(d) === 'dim' && isLightMode) {
            return d3.color(color).darker(1.4).formatRgb() //darken unhighlighted cells
          }
          return color
        })
        .style('opacity', (d) => (!isLightMode ? highlightOpacity(d) : 1))

      //Unselected base
      g.selectAll('.data-point-unselected-base')
        .data(mergedData.filter((d) => d.group === 'unselected'))
        .enter()
        .append('rect')
        .attr('class', 'data-point-unselected-base')
        .attr('x', getX)
        .attr('y', getY)
        .attr('width', getWidth)
        .attr('height', getHeight)
        .style('fill', (d) => {
          const color = unselectedColorScale(d.value)
          if (highlightOpacity(d) === 'dim') {
            return isLightMode ? d3.color(color).darker(1.4).formatRgb() : color
          }
          return color
        })
        .style('opacity', (d) => (!isLightMode ? highlightOpacity(d) : 1))
        .on('click', onClickHandler)

      //Unselected hatch overlay
      g.selectAll('.data-point-unselected-hatch')
        .data(mergedData.filter((d) => d.group === 'unselected'))
        .enter()
        .append('rect')
        .attr('class', 'data-point-unselected-hatch')
        .attr('x', getX)
        .attr('y', getY)
        .attr('width', getWidth)
        .attr('height', getHeight)
        .style('fill', 'url(#diagonalHatchWhite)')
        .style('opacity', (d) => {
          if (highlightOpacity(d) === 'dim') {
            return isLightMode ? 0.15 : highlightOpacity(d) //dim hatch lightly in light mode
          }
          return 1
        })
        .on('click', onClickHandler)

      //Excluded base
      g.selectAll('.data-point-excluded-base')
        .data(mergedData.filter((d) => d.group === 'excluded'))
        .enter()
        .append('rect')
        .attr('class', 'data-point-excluded-base')
        .attr('x', getX)
        .attr('y', getY)
        .attr('width', getWidth)
        .attr('height', getHeight)
        .style('fill', (d) => {
          const color = excludedColorScale(d.value)
          if (highlightOpacity(d) === 'dim') {
            return isLightMode ? d3.color(color).darker(1.4).formatRgb() : color
          }
          return color
        })
        .style('opacity', (d) => (!isLightMode ? highlightOpacity(d) : 1))
        .on('click', onClickHandler)

      //Excluded hatch overlay
      g.selectAll('.data-point-excluded-hatch')
        .data(mergedData.filter((d) => d.group === 'excluded'))
        .enter()
        .append('rect')
        .attr('class', 'data-point-excluded-hatch')
        .attr('x', getX)
        .attr('y', getY)
        .attr('width', getWidth)
        .attr('height', getHeight)
        .style('fill', 'url(#diagonalHatchBlack)')
        .style('opacity', (d) => {
          if (highlightOpacity(d) === 'dim') {
            return isLightMode ? 0.15 : highlightOpacity(d) //light dim hatch in light mode
          }
          return 1
        })
        .on('click', onClickHandler)

      highlightSelection(props.selection)
    }

    const toggleCollapsedColumn = (j) => {
      //change color to gray when collapsing was changed by selecting
      attributionSliderColor.value = '#6e6e6e'
      if (collapsed.value.columns.includes(j)) {
        collapsed.value.columns = collapsed.value.columns.filter((col) => col !== j)
      } else {
        if (collapsed.value.columns.length < props.attributionModel.tokens_b.length - 1) {
          collapsed.value.columns.push(j)
        }
      }
      createChart()
    }

    const toggleCollapsedRow = (i) => {
      if (collapsed.value.rows.includes(i)) {
        collapsed.value.rows = collapsed.value.rows.filter((row) => row !== i)
      } else {
        if (collapsed.value.rows.length < props.attributionModel.tokens_a.length - 1) {
          collapsed.value.rows.push(i)
        }
      }
      createChart()
    }

    const onClickHandler = (event, d) => {
      selectedTokens.value.tokens_a = []
      selectedTokens.value.tokens_b = []

      if (event.shiftKey) {
        selectedTokens.value.tokens_b.push(d.j)
      } else {
        selectedTokens.value.tokens_a.push(props.attributionModel.tokens_a.length - d.i - 1)
      }

      emit('selection-changed', {
        tokens_a: [...selectedTokens.value.tokens_a],
        tokens_b: [...selectedTokens.value.tokens_b],
      })
    }

    const highlightSelection = (selection) => {
      const svg = d3.select(chart.value).select('svg')
      const g = svg.select('g')

      const tokens_a = props.attributionModel.tokens_a

      const { xScale, yScale } = getAdjustedScales()

      let indices, axis
      if (selection.tokens_a && selection.tokens_a.length > 0) {
        indices = selection.tokens_a
        axis = 'y'
      } else if (selection.tokens_b && selection.tokens_b.length > 0) {
        indices = selection.tokens_b
        axis = 'x'
      } else {
        //no selection
        g.selectAll('.highlight-rect').remove()
        return
      }

      const sorted = [...indices].sort((a, b) => a - b)
      const first = sorted[0]
      const last = sorted[sorted.length - 1]

      let start, end
      if (axis === 'x') {
        start = xScale(first)
        end = xScale(last) + xScale.bandwidthAt(last)
      } else {
        //invert the indices for the yaxis
        const invertedFirst = tokens_a.length - 1 - first
        const invertedLast = tokens_a.length - 1 - last
        start = yScale(invertedFirst)
        end = yScale(invertedLast) + yScale.bandwidthAt(invertedLast)
      }

      g.selectAll('.highlight-rect').remove()
      g.append('rect')
        .attr('class', 'highlight-rect')
        .attr(axis === 'x' ? 'x' : 'y', start)
        .attr(axis === 'x' ? 'y' : 'x', 0)
        .attr('width', axis === 'x' ? end - start : chartWidth)
        .attr('height', axis === 'x' ? chartHeight : end - start)
        .attr('fill', 'none')
        .attr('stroke', 'rgba(0,255,125,0.5)')
        .attr('stroke-width', 3)
    }

    watch(
      () => [
        props.attributionModel,
        props.bounds,
        props.negativeBounds,
        collapseThresholdMode.value,
      ],
      () => {
        //redraw collapsed charts
        collapseLowAttributionRowsAndColumns()
      },
      { deep: true },
    )

    watch(
      () => props.selection,
      () => {
        selectedTokens.value = {
          tokens_a: [...props.selection.tokens_a],
          tokens_b: [...props.selection.tokens_b],
        }

        highlightSelection(props.selection)
      },
      { deep: true },
    )

    function updateCollapsed(newCollapsed) {
      //change color to gray when collapsing was changed by selecting
      attributionSliderColor.value = '#6e6e6e'
      collapsed.value = newCollapsed
      createChart()
    }

    function updateHighlight(tag) {
      highlightedPOSTag.value = tag
      createChart()
    }

    const collapseLowAttributionRowsAndColumns = (threshold = collapseThreshold.value) => {
      //change to default color to show that the threshold is applied
      attributionSliderColor.value = null
      const { attributions, tokens_a, tokens_b } = props.attributionModel

      const oldCollapsed = {
        rows: [...collapsed.value.rows],
        columns: [...collapsed.value.columns],
      }
      let newCollapsed = {
        rows: [],
        columns: [],
      }

      const transformedAttributeValues = (val) => {
        switch (collapseThresholdMode.value) {
          case 0: //absolute
            return Math.abs(val)
          case 1: //normal
            return val
          case 2: //inverted
            return -val
          default:
            return Math.abs(val)
        }
      }

      //Check rows and cols
      for (let i = 0; i < tokens_a?.length; i++) {
        const row = attributions[i]
        const maxInRow = Math.max(...row.map(transformedAttributeValues))
        if (maxInRow < threshold && !newCollapsed.rows.includes(i)) {
          newCollapsed.rows.push(i)
        }
      }

      for (let j = 0; j < tokens_b?.length; j++) {
        const column = attributions.map((row) => row[j])
        const maxInColumn = Math.max(...column.map(transformedAttributeValues))
        if (maxInColumn < threshold && !newCollapsed.columns.includes(j)) {
          newCollapsed.columns.push(j)
        }
      }

      //if all should be collapsed, collapse none
      if (
        newCollapsed.rows.length == tokens_a?.length &&
        newCollapsed.columns.length == tokens_b?.length
      ) {
        newCollapsed = {
          rows: [],
          columns: [],
        }
      }

      //apply new collapsed value but only if it changed, to improve performance on watchers of this prop
      if (
        !arraysEqual(newCollapsed.rows, oldCollapsed.rows) ||
        !arraysEqual(newCollapsed.columns, oldCollapsed.columns)
      ) {
        collapsed.value = newCollapsed
      }
      createChart()
    }

    function updateThreshold() {
      const attributions = props.attributionModel?.attributions
      if (!attributions) return
      const quantile = computeQuantile(attributions)
      collapseThresholdPosition.value = Math.pow(quantile, 1 / 3)
      collapseLowAttributionRowsAndColumns()
    }

    onMounted(() => {
      updateThreshold()
    })

    watch(
      () => props.attributionModel,
      () => {
        updateThreshold()
      },
      { deep: true },
    )

    return {
      chart,
      collapseLowAttributionRowsAndColumns,
      collapseThreshold,
      collapseThresholdText,
      collapseThresholdPosition,
      collapsed,
      updateCollapsed,
      attributionSliderColor,
      collapseThresholdMode,
      updateHighlight,
    }
  },
}
</script>
