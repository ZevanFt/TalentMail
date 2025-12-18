<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const toggle = () => {
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <button @click="toggle" class="relative w-11 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary/20"
    :class="modelValue ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'">
    <span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
      :class="modelValue ? 'translate-x-5' : 'translate-x-0'"></span>
  </button>
</template>