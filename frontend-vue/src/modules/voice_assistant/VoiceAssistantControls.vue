<script setup lang="ts">
import { computed } from 'vue'
import { useVoiceAssistantControl } from '@/modules/voice_assistant/composables/useVoiceAssistantControl.ts'
import { useChat } from '@/modules/chat/composables/useChat.ts'
import type { MessageType } from '@/types/chat.ts'

const {
  isLoading,
  lastMessage,
  lastError,
  activateAssistant,
  cancelListening,
  toggleWakeword,
} = useVoiceAssistantControl()

const { addMessage } = useChat()


async function onActivateClick() {
  const res = await activateAssistant()
  if (res && res.message) {
    const type: MessageType = res.status === 'activated' ? 'info' : 'error'
    addMessage(res.message, type)
  }
}

async function onCancelClick() {
  const res = await cancelListening()
  if (res && res.message) {
    const type: MessageType = res.status === 'cancelled' ? 'info' : 'error'
    addMessage(res.message, type)
  }
}

async function onToggleWakewordClick() {
  const res = await toggleWakeword()
  if (res && res.message) {
    const type: MessageType = res.status === 'success' ? 'info' : 'error'
    addMessage(res.message, type)
  }
}


// Пример текста статуса для вывода
const statusText = computed(() => {
  if (lastError.value) return lastError.value
  if (lastMessage.value) return lastMessage.value
  return 'Нет последних сообщений'
})
</script>

<template>
  <div class="flex flex-col gap-4 p-4 border border-zinc-700/70 bg-zinc-800/40 rounded-xl shadow-md min-w-[260px]">
    <h2 class="text-lg font-semibold">Управление ассистентом</h2>

    <div class="flex flex-col gap-2">
      <button
        class="w-full px-4 py-2 rounded-lg bg-indigo-700/40 text-white hover:bg-indigo-600 transition disabled:opacity-60"
        :disabled="isLoading"
        @click="onActivateClick"
      >
        Активировать прослушивание
      </button>

      <button
        class="w-full px-4 py-2 rounded-lg bg-red-600/50 text-white hover:bg-red-500 transition disabled:opacity-60"
        :disabled="isLoading"
        @click="onCancelClick"
      >
        Отменить команду
      </button>

      <button
        class="w-full px-4 py-2 rounded-lg bg-gray-200/40 hover:bg-gray-300 transition disabled:opacity-60"
        :disabled="isLoading"
        @click="onToggleWakewordClick"
      >
        Переключить wakeword (мут/анмут)
      </button>
    </div>

    <p class="text-xs text-gray-500">
      {{ statusText }}
    </p>
  </div>
</template>
