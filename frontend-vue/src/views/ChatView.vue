<script setup lang="ts">
import Chat from '@/modules/chat/Chat.vue'

import { apiClient } from '@/modules/voice_assistant/api/apiClient.ts'

async function testStatus() {
  try {
    const status = await apiClient.getStatus()
    console.log('STATUS FROM SERVER:', status)
  } catch (e) {
    console.error('Ошибка getStatus', e)
  }
}
</script>

<template>
  <div class="h-[calc(50vh-64px)]">
    <Chat />

    <button
      class="px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
      @click="testStatus"
    >
      Проверить статус
    </button>
  </div>
</template>

<style scoped></style>
