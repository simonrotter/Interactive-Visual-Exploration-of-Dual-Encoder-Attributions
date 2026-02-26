<template>
  <div
    class="pos-toggle"
    :class="{
      checked: state === 'checked',
      unchecked: state === 'unchecked',
      indeterminate: state === 'indeterminate',
    }"
    @click="toggle"
  >
    {{ label }}
  </div>
</template>

<script setup>
//dumb three state toggle with no logic, just looks neat
defineProps({
  label: String,
  state: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['toggle'])

function toggle(event) {
  event.stopPropagation()
  emit('toggle')
}
</script>

<style scoped>
.pos-toggle {
  display: inline-block;
  padding: 0.3rem 0.75rem;
  border-radius: 9px;
  cursor: pointer;
  user-select: none;
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0.25rem;
  transition:
    background-color 0.2s,
    color 0.2s;
}

.checked {
  background-color: #517373;
  color: white;
}

.unchecked {
  background-color: #5d5d5d;
  color: white;
}

.indeterminate {
  background: repeating-linear-gradient(135deg, #3f3f3f, #3f3f3f 4px, #5a8585 4px, #5a8585 8px);
  color: white;
  text-shadow: 1px 1px 10px #000000a2;
}

/* Light mode override */
@media (prefers-color-scheme: light) {
  .unchecked {
    background-color: #c6c6c6;
    color: black;
  }

  .indeterminate {
    background: repeating-linear-gradient(135deg, #d0d0d0, #d0d0d0 4px, #a8c0c0 4px, #a8c0c0 8px);
    color: rgb(0, 0, 0);
    text-shadow: none;
  }
}
</style>
