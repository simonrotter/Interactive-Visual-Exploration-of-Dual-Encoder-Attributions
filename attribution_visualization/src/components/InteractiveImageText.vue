<template>
  <div>
    <div ref="textChart"></div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'
//adapted version of interactivetext only using one line, shares parts
export default {
  name: 'TextChart',
  props: {
    tokenModel: {
      type: Object,
      required: true,
    },
    selection: {
      type: Object,
      required: true,
    },
    showcolors: {
      type: Boolean,
      required: false,
      default: true,
    },
    imageAttributions: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  setup(props, { emit }) {
    const textChart = ref()
    const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

    onMounted(() => {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        isDarkMode.value = e.matches
      })
    })

    const createTokenSelection = () => {
      const tokens_a = props.tokenModel?.tokens_a
      const tokens_b = props.tokenModel?.tokens_b
      let container = d3.select(textChart.value)

      container.selectAll('.token-row').remove()

      const updateSelectionStyles = () => {
        container.selectAll('.token').classed('selected', function (_, i) {
          const rowType = d3.select(this).attr('data-row')
          return (
            (rowType === 'a' && props.selection.tokens_a.includes(i)) ||
            (rowType === 'b' && props.selection.tokens_b.includes(i - tokens_a.length))
          )
        })
      }

      const detectSelectedTokens = (e) => {
        const selection = window.getSelection()
        if (!selection.rangeCount) return
        const range = selection.getRangeAt(0)
        selection.removeAllRanges()

        const ctrlKey = e.ctrlKey || e.metaKey //mataKey is mac ctrl
        const newSelection = { tokens_a: [], tokens_b: [] }
        let selectedInA = false

        container.selectAll('.token').each(function (d, i) {
          const tokenBox = this.getBoundingClientRect()
          const selectionBox = range.getBoundingClientRect()
          const rowType = d3.select(this).attr('data-row')
          if (
            selectionBox.right > tokenBox.left &&
            selectionBox.left < tokenBox.right &&
            selectionBox.bottom > tokenBox.top &&
            selectionBox.top < tokenBox.bottom
          ) {
            if (rowType === 'a') {
              newSelection.tokens_a.push(i)
              selectedInA = true
            }
            if (rowType === 'b') {
              const bIndex = i - props.tokenModel.tokens_a.length
              newSelection.tokens_b.push(bIndex)
            }
          }
        })

        let finalSelection = { tokens_a: [], tokens_b: [] }

        if (ctrlKey) {
          //create edit copy
          finalSelection.tokens_a = [...props.selection.tokens_a]
          finalSelection.tokens_b = [...props.selection.tokens_b]

          const toggleTokens = (existing, toToggle) =>
            Array.from(
              new Set([
                ...existing.filter((t) => !toToggle.includes(t)), //remove if exists
                ...toToggle.filter((t) => !existing.includes(t)), //add if not exists
              ]),
            ).sort((a, b) => a - b)

          if (selectedInA) {
            finalSelection.tokens_a = toggleTokens(finalSelection.tokens_a, newSelection.tokens_a)
            finalSelection.tokens_b = []
          } else {
            finalSelection.tokens_b = toggleTokens(finalSelection.tokens_b, newSelection.tokens_b)
            finalSelection.tokens_a = []
          }
        } else {
          finalSelection = newSelection
        }

        updateSelectionStyles()
        emit('selection-changed', finalSelection)
      }

      const rowA = container.append('div').attr('class', 'token-row').style('margin-bottom', '10px')
      rowA
        .selectAll('.token')
        .data(tokens_a)
        .enter()
        .append('span')
        .attr('class', 'token')
        .attr('data-row', 'a')
        .style('margin-right', '5px')
        .text((d) => d)

      const rowB = container.append('div').attr('class', 'token-row')
      rowB
        .selectAll('.token')
        .data(tokens_b)
        .enter()
        .append('span')
        .attr('class', 'token')
        .attr('data-row', 'b')
        .style('margin-right', '5px')
        .text((d) => d)

      d3.select(window).on('mouseup', (event) => detectSelectedTokens(event))

      if (!document.querySelector('#tokenStyles')) {
        const styleTag = document.createElement('style')
        styleTag.id = 'tokenStyles'
        styleTag.innerHTML = `
            .token.selected {
              border-radius: 3px;
              padding: 2px;
            }
          `
        document.head.appendChild(styleTag)
      }
    }

    const clearSelection = () => {
      emit('selection-changed', { tokens_a: [], tokens_b: [] })
    }

    const getColorFromValue = (value, maxAbs) => {
      if (maxAbs === 0) return 'rgb(255,255,255)'
      const normVal = Math.sign(value) * Math.sqrt(Math.abs(value) / maxAbs)
      return isDarkMode.value ? darkModeColors(normVal) : lightModeColors(normVal)
    }

    const darkModeColors = (value) => {
      const b = Math.round(255 * (-1 * Math.min(0, value)))
      const r = Math.round(255 * Math.max(0, value))
      return `rgb(${r}, 0, ${b})`
    }

    const lightModeColors = (value) => {
      const b = Math.round(255 - 255 * Math.max(0, value))
      const r = Math.round(255 - 255 * (-1 * Math.min(0, value)))
      const g = Math.min(r, b)
      return `rgb(${r}, ${g}, ${b})`
    }

    const applyTokenColors = (values, rowType) => {
      const maxAbs = Math.max(...values.map(Math.abs), 1e-6)

      d3.select(textChart.value)
        .selectAll(`.token[data-row="${rowType}"]`)
        .style('background-color', (d, i) => {
          return props.showcolors ? getColorFromValue(values[i] || 0, maxAbs) : 'transparent'
        })
        .style('border', (d, i) => {
          const isSelected =
            rowType === 'a'
              ? props.selection.tokens_a.includes(i)
              : props.selection.tokens_b.includes(i)
          return isSelected ? '2px solid rgba(0, 200, 100, 1)' : '2px solid rgba(0, 0, 0, 0)'
        })
        .style('box-sizing', 'border-box')
        .style('border-radius', '5px')
        .style('padding', '0px 4px')
    }

    const computeTokenImageAttributions = () => {
      const maps = props.imageAttributions
      if (!maps.length) return []

      return maps.map((tokenMap) => {
        let sum = 0
        for (let i = 0; i < tokenMap.length; i++) {
          for (let j = 0; j < tokenMap[0].length; j++) {
            sum += tokenMap[i][j]
          }
        }
        return sum
      })
    }

    watch(
      [() => props.selection],
      () => {
        createTokenSelection()
        const tokenAttributions = computeTokenImageAttributions()
        applyTokenColors(tokenAttributions, 'a')
      },
      { deep: true },
    )

    watch(
      [() => props.imageAttributions],
      () => {
        clearSelection()
        createTokenSelection()
        const tokenAttributions = computeTokenImageAttributions()
        applyTokenColors(tokenAttributions, 'a')
      },
      { deep: true },
    )

    return {
      textChart,
      clearSelection,
    }
  },
}
</script>

<style scoped>
.token.selected {
  border-radius: 3px;
  padding: 2px;
}
</style>
