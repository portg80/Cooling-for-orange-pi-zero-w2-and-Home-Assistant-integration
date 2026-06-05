<script setup lang="ts">
  import { defineProps, defineEmits } from 'vue'
  import { useAssistantStore } from '@/stores/assistantStore.ts'

  const assistantStore = useAssistantStore()

  const emits = defineEmits<{
    (e: 'collapseall'):void
  }>()
</script>

<template>
  <!-- Панель снизу -->
  <div class="flex items-center justify-between pt-2 text-sm text-gray-100">
    <div class="flex items-center gap-2">
      <span>Чат ассистента</span>
      <span
        class="px-2 py-0.5 rounded text-xs"
        :class="assistantStore.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
      >
      {{ assistantStore.isActive ? 'Активен' : 'Выключен' }}
    </span>
    </div>

    <div class="flex items-center gap-1 text-xs text-gray-100">
      <span>Состояние:</span>
      <span class="w-2 h-2 rounded-full" :class="waveStateClass"></span>
    </div>

    <div class="flex items-center gap-2">
      <button
        class="px-2 py-1 rounded bg-gray-500/40 hover:bg-gray-500/60"
        @click="emits('collapseall')"
      >
        Свернуть все
      </button>
    </div>
  </div>
</template>

<style scoped>

</style>
