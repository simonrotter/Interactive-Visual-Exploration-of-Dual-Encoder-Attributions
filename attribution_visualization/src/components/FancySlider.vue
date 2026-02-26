<template>
  <div class="relative">
    <PercentageBar
      :value="normalizedValue"
      class="block"
      :hidePercentage="true"
      :customText="text"
      :transitionEnabled="false"
      :color="color ?? '#5a8585'"
    />
    <input
      type="range"
      :min="min"
      :max="max"
      :value="modelValue"
      @input="onInput"
      class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
      :step="step"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import PercentageBar from './PercentageBar.vue'

//slider building on top of the percentagebar design
const props = defineProps({
  modelValue: {
    type: Number,
    required: true,
  },
  min: {
    type: Number,
    default: 0,
  },
  max: {
    type: Number,
    required: true,
  },
  text: {
    type: String,
    default: '',
  },
  step: {
    type: Number,
    default: 0.5,
  },
  color: {
    type: String,
    default: '#5a8585',
  },
})

const emit = defineEmits(['update:modelValue', 'input'])

//normalized ratio
const normalizedValue = computed(() => {
  if (props.max === props.min) return 0
  return props.modelValue / (props.max - props.min)
})

//pass thru slider behavior
function onInput(event) {
  const newValue = Number(event.target.value)
  emit('update:modelValue', newValue)
  emit('input', newValue / (props.max - props.min))
}
</script>
