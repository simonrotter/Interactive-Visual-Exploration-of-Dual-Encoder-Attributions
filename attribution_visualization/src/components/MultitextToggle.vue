<template>
  <div class="relative flex cursor-pointer" @click="propagationStop">
    <div
      class="relative flex items-center w-max bg-neutral-200 dark:bg-neutral-700 bg-opacity-50 cursor-pointer transition-all duration-[400ms] ease overflow-hidden px-3 py-0 rounded-[11px]"
      ref="background"
    >
      <!-- pill that highlights the selected label -->
      <div
        class="absolute h-7 transition-all duration-[400ms] ease mx-1 my-0 rounded-[9px]"
        :style="pillStyle"
        :class="{
          'bg-neutral-500 bg-opacity-50': disabled,
          'bg-blue-600': !disabled,
        }"
      ></div>
      <div
        v-for="(label, index) in labels"
        :key="index"
        ref="labelText"
        class="toggle-text"
        :style="[getTextStyle(index), { marginRight: index < labels.length - 1 ? '15px' : '0' }]"
        @click="toggleSwitch(index)"
      >
        {{ label }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.toggle-text {
  @apply relative text-sm leading-9 transition-[0.4s] whitespace-nowrap w-max select-none;
}
</style>

<script>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

export default {
  props: {
    modelValue: {
      type: Number,
      default: 0, //by default selecting the first label
    },
    labels: {
      type: Array,
      default: () => ['Aus', 'Ein'],
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  setup(props, { emit }) {
    const background = ref(null)
    const labelRefs = ref([]) //Ref array for each labels DOM
    const selectedIndex = ref(props.modelValue)

    //Watch modelValue to sync with the parent component
    watch(
      () => props.modelValue,
      (newVal) => {
        selectedIndex.value = newVal
        emit('change', selectedIndex.value)
      },
    )

    //Compute pill style to adapt in width
    const pillStyle = computed(() => {
      if (labelRefs.value.length === 0) return {}

      //Calculate the width and position of the pill based on the selected label
      const selectedLabel = labelRefs.value[selectedIndex.value]
      const leftOffset = selectedLabel ? selectedLabel.offsetLeft - 12 : 0
      const width = selectedLabel ? selectedLabel.offsetWidth + 15 : 0

      return {
        left: `${leftOffset}px`,
        width: `${width}px`,
      }
    })

    const getTextStyle = (index) => {
      return {
        color: selectedIndex.value === index ? 'white' : '',
      }
    }

    const toggleSwitch = (index) => {
      if (!props.disabled && index !== selectedIndex.value) {
        selectedIndex.value = index
      }
    }

    //Prevent click event propagation
    const propagationStop = (click) => {
      click.stopPropagation()
    }

    //Watch labels array for changes and update label widths
    watch(
      () => props.labels,
      () => {
        nextTick(() => {
          updateLabelWidths()
        })
      },
      { immediate: true },
    )

    //Update the widths of the labels
    const updateLabelWidths = () => {
      if (background.value) {
        labelRefs.value = Array.from(background.value.querySelectorAll('.toggle-text'))
      }
    }

    onMounted(() => {
      nextTick(() => {
        updateLabelWidths()
      })
    })

    //Sync the selectedIndex with the parent via v-model
    watch(selectedIndex, (newValue) => {
      emit('update:modelValue', newValue)
    })

    return {
      background,
      labelRefs,
      selectedIndex,
      pillStyle,
      getTextStyle,
      toggleSwitch,
      propagationStop,
    }
  },
}
</script>
