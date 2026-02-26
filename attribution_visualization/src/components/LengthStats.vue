<template>
  <div ref="chartRef" class="h-[700px] relative">
    <div
      v-if="tooltip.visible"
      :style="tooltip.style"
      class="absolute rounded shadow-md text-sm p-2 pointer-events-none z-10 max-w-sm tooltip-box"
    >
      {{ tooltip.data.text_a }}<br /><br />
      {{ tooltip.data.text_b }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import * as d3 from 'd3'
import { fetchLengthStats, fetchTexts } from '../js/backendUtils.js'
//overview diagram
const emit = defineEmits(['pointClicked'])

const chartRef = ref(null)
const tooltip = reactive({
  visible: false,
  style: {
    left: '0px',
    top: '0px',
  },
  data: {
    index: null,
    text_a: '',
    text_b: '',
  },
})

onMounted(async () => {
  const [stats, texts] = await Promise.all([fetchLengthStats(), fetchTexts()])
  if (!stats || !texts) return

  const data = stats.map((item) => {
    const textData = texts.find((t) => t.index === item.index)
    return {
      ...item,
      text_a: textData?.text_a,
      text_b: textData?.text_b,
    }
  })

  drawScatterplot(data)
})

function drawScatterplot(data) {
  const margin = { top: 20, right: 30, bottom: 40, left: 50 }
  const outerWidth = 1200
  const outerHeight = 700
  const width = outerWidth - margin.left - margin.right
  const height = outerHeight - margin.top - margin.bottom

  const root = d3
    .select(chartRef.value)
    .append('svg')
    .attr('width', outerWidth)
    .attr('height', outerHeight)
    .style('touch-action', 'none')
    .style('cursor', 'grab')

  const svg = root.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const filteredData = data.filter((d) => d.length_ratio !== null && d.length_ratio > 0)

  const logRatios = filteredData.map((d) => Math.log(d.length_ratio))
  const maxAbs = d3.max(logRatios, (d) => Math.abs(d))

  const x = d3.scaleLinear().domain([-maxAbs, maxAbs]).range([0, width])
  const y = d3
    .scaleLinear()
    .domain(d3.extent(filteredData, (d) => d.sum_attributions))
    .nice()
    .range([height, 0])

  const xAxis = d3.axisBottom(x).tickFormat((d) => Math.exp(d).toFixed(2))
  const yAxis = d3.axisLeft(y)

  const gx = svg.append('g').attr('transform', `translate(0,${height})`).call(xAxis)
  const gy = svg.append('g').call(yAxis)

  gx.attr('pointer-events', 'none')
  gy.attr('pointer-events', 'none')

  svg
    .append('text')
    .attr('x', width / 2)
    .attr('y', height + 35)
    .attr('text-anchor', 'middle')
    .text('Word count ratio (len_a / len_b)')

  svg
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', -40)
    .attr('x', -height / 2)
    .attr('text-anchor', 'middle')
    .text('Attribution sum')

  const maxAbsAttrib = d3.max(filteredData, (d) => Math.abs(d.sum_attributions))
  const color = d3
    .scaleSymlog()
    .domain([-maxAbsAttrib, 0, maxAbsAttrib])
    .range(['#3b82f6', '#dbdbdb', '#ef4444'])

  //Clip so points dont overflow when panning
  const clipId = `clip-${Math.random().toString(36).slice(2)}`
  const clipPadding = 4

  root
    .append('defs')
    .append('clipPath')
    .attr('id', clipId)
    .append('rect')
    .attr('x', -clipPadding)
    .attr('y', -clipPadding)
    .attr('width', width + 2 * clipPadding)
    .attr('height', height + 2 * clipPadding)

  const hitRect = svg
    .append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .style('pointer-events', 'all')

  const plot = svg.append('g').attr('clip-path', `url(#${clipId})`)
  const scatterGroup = plot.append('g').attr('class', 'scatter-group')

  const circles = scatterGroup
    .selectAll('circle')
    .data(filteredData)
    .enter()
    .append('circle')
    .attr('cx', (d) => x(Math.log(d.length_ratio)))
    .attr('cy', (d) => y(d.sum_attributions))
    .attr('r', 4)
    .attr('fill', (d) => color(d.sum_attributions))
    .attr('opacity', 0.75)
    .on('mouseover', function (event, d) {
      tooltip.visible = true
      tooltip.data = {
        index: d.index,
        text_a: d.text_a,
        text_b: d.text_b,
      }

      //get mouse coords relative to the SVG root NOT the diagram
      const [xPos, yPos] = d3.pointer(event, root.node())
      tooltip.style.left = `${xPos + 10}px`
      tooltip.style.top = `${yPos + 10}px`
      root.style('cursor', 'pointer')
    })
    .on('mousemove', function (event) {
      const [xPos, yPos] = d3.pointer(event, root.node())
      tooltip.style.left = `${xPos + 10}px`
      tooltip.style.top = `${yPos + 10}px`
    })
    .on('mouseout', () => {
      tooltip.visible = false
      root.style('cursor', 'grab')
    })
    .on('click', (event, d) => {
      emit('pointClicked', d.index)
    })

  const baseRadius = 4

  const zoom = d3
    .zoom()
    .scaleExtent([1, 12])
    .translateExtent([
      [0, 0],
      [width, height],
    ])
    .extent([
      [0, 0],
      [width, height],
    ])
    .filter((event) => {
      if (event.type === 'wheel') return true
      if (event.type === 'mousedown') return event.button === 0
      if (event.type === 'touchstart') return true
      return false
    })
    .wheelDelta((event) => {
      const m = event.deltaMode === 1 ? 0.05 : event.deltaMode === 2 ? 1 : 0.0025
      return -event.deltaY * m
    })
    .on('start', () => root.style('cursor', 'grabbing'))
    .on('end', () => root.style('cursor', 'grab'))
    .on('zoom', (event) => {
      const t = event.transform
      scatterGroup.attr('transform', t)

      gx.call(xAxis.scale(t.rescaleX(x)))
      gy.call(yAxis.scale(t.rescaleY(y)))

      //after zoom use same circle size again
      circles.attr('r', baseRadius / t.k)
    })

  svg.call(zoom)
  hitRect.call(zoom)
}
</script>

<style scoped>
circle:hover {
  stroke: black;
  stroke-width: 1.5px;
}

.tooltip-box {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px) contrast(60%);
  color: white;
}

@media (prefers-color-scheme: light) {
  .tooltip-box {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(20px) contrast(80%);
    color: black;
  }
}
</style>
