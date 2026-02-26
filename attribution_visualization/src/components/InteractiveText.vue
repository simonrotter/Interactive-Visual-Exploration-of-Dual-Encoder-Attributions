<template>
  <div>
    <div ref="textChart"></div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'

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
    showReverseAttrib: {
      type: Boolean,
      default: false,
    },
  },
  setup(props, { emit }) {
    const textChart = ref()
    const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

    //this components does not update its visualization (selection coloring / (reverse-) attribution coloring) when itself triggers the change (selcetion changes or is cleared)
    //the change is only emitted back to the parent component which is expected to update this components props.
    //so this component only visualizes and updates on the two prop values
    //this decision was made because changing visualization depending on the prop and also internally would create confusion and double changes everytime this component changes the selection

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

        const ctrlKey = e.ctrlKey || e.metaKey
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

    //attribution values summed up for all a tokens
    //all selected a tokens' attributions towards b_tokens are summed up. the result is the length of b_tokens and therefore can be mapped to them
    const computeAveragedAttributionsForAtokens = (indexList) => {
      const attributions = props.tokenModel.attributions
      const numSelected = indexList.length
      if (numSelected === 0) return new Array(attributions[0].length).fill(0)
      const yLength = attributions[0].length
      const result = new Array(yLength).fill(0)
      indexList.forEach((xIndex) => {
        attributions[xIndex].forEach((value, yIndex) => {
          result[yIndex] += value
        })
      })
      return result.map((val) => val / numSelected)
    }

    const computeAveragedAttributionsForBtokens = (indexList) => {
      const attributions = props.tokenModel.attributions
      const numSelected = indexList.length
      if (numSelected === 0) return new Array(attributions.length).fill(0)
      const xLength = attributions.length
      const result = new Array(xLength).fill(0)
      attributions.forEach((attrList, xIndex) => {
        attrList.forEach((value, yIndex) => {
          if (indexList.includes(yIndex)) {
            result[xIndex] += value
          }
        })
      })
      return result.map((val) => val / numSelected)
    }

    //reverse attribution from the same token list as the the selcted tokens
    const computeReverseAttribution = () => {
      const model = props.tokenModel
      const reversed = true
      const tokens_a = reversed ? model.tokens_a.slice().reverse() : model.tokens_a
      const tokens_b = model.tokens_b
      const attributions = model.attributions
      const selectedA = props.selection.tokens_a
      const selectedB = props.selection.tokens_b

      if (selectedA.length > 0) {
        //Forward attribution on tokens_b (normal)
        let forwardOnB = Array(tokens_b.length).fill(0)
        selectedA.forEach((tokenIndex) => {
          const actualAIndex = reversed ? tokens_a.length - 1 - tokenIndex : tokenIndex
          const weights = attributions[actualAIndex]
          forwardOnB = weights.map((val, i) => val + forwardOnB[i])
        })
        forwardOnB = forwardOnB.map((val) => val / selectedA.length)

        //Reverse attribution back on tokens_a (from tokens_b)
        let reverseOnA = Array(tokens_a.length).fill(0)
        forwardOnB.forEach((weightB, bIndex) => {
          for (let aIndex = 0; aIndex < tokens_a.length; aIndex++) {
            const actualAIndex = reversed ? tokens_a.length - 1 - aIndex : aIndex
            //Here we use attribution from actualAIndex to bIndex, weighted by forward weightB
            reverseOnA[aIndex] += weightB * attributions[actualAIndex][bIndex]
          }
        })

        return [reverseOnA, forwardOnB]
      }

      if (selectedB.length > 0) {
        //Forward attribution on tokens_a (normal)
        let forwardOnA = Array(tokens_a.length).fill(0)
        selectedB.forEach((tokenIndexB) => {
          for (let i = 0; i < tokens_a.length; i++) {
            const actualAIndex = reversed ? tokens_a.length - 1 - i : i
            forwardOnA[i] += attributions[actualAIndex][tokenIndexB]
          }
        })
        forwardOnA = forwardOnA.map((val) => val / selectedB.length)

        //Reverse attribution back on tokens_b (from tokens_a)
        let reverseOnB = Array(tokens_b.length).fill(0)
        forwardOnA.forEach((weightA, aIndex) => {
          for (let bIndex = 0; bIndex < tokens_b.length; bIndex++) {
            const actualAIndex = reversed ? tokens_a.length - 1 - aIndex : aIndex
            //attribution from actualAIndex to bIndex weighted by weightA
            reverseOnB[bIndex] += weightA * attributions[actualAIndex][bIndex]
          }
        })

        return [forwardOnA, reverseOnB]
      }

      return [Array(tokens_a.length).fill(0), Array(tokens_b.length).fill(0)]
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

    const applyTokenColors = (colors, rowType, maxAbs) => {
      d3.select(textChart.value)
        .selectAll(`.token[data-row="${rowType}"]`)
        .style('background-color', (d, i) => {
          const bg = getColorFromValue(colors[i] || 0, maxAbs)
          return bg
        })
        .style('color', (d, i) => {
          const bg = getColorFromValue(colors[i] || 0, maxAbs)
          const rgb = bg.match(/\d+/g).map(Number)
          const brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
          return brightness > 150 ? '#000' : '#fff'
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

    watch(
      [() => props.tokenModel, () => props.selection],
      () => {
        createTokenSelection()
      },
      { deep: true },
    )

    watch(
      [() => props.selection, () => props.showReverseAttrib],
      () => {
        updateColors()
      },
      { deep: true },
    )

    return {
      textChart,
    }

    function updateColors() {
      let aColors = computeAveragedAttributionsForAtokens(props.selection.tokens_a)
      let bColors = computeAveragedAttributionsForBtokens(props.selection.tokens_b)

      const [reverseAtoB, reverseBtoA] = computeReverseAttribution()

      //if enabled show the pingpong atribution
      if (props.showReverseAttrib) {
        bColors = bColors.map((val, i) => val + reverseAtoB[i])
        aColors = aColors.map((val, i) => val + reverseBtoA[i])
      }

      const allValues = [...aColors, ...bColors]
      const maxAbs = Math.max(...allValues.map(Math.abs)) || 1

      applyTokenColors(aColors, 'b', maxAbs)
      applyTokenColors(bColors, 'a', maxAbs)
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
