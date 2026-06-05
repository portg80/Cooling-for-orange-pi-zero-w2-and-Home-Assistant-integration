<script setup lang="ts">
import { ref, nextTick, computed, onMounted, onBeforeUnmount  } from 'vue'
import ChatInput from '@/modules/chat/components/UI/ChatInput.vue'
import ChatMessageBubble from '@/modules/chat/components/ChatMessageBubble.vue'
import type { ChatMessage, MessageType } from '@/types/chat.ts'
import { useChat } from '@/modules/chat/composables/useChat.ts'
import { useAssistantStore } from '@/stores/assistantStore.ts'
import ChatInfoPanel from '@/modules/chat/components/ChatInfoPanel.vue'

const assistantStore = useAssistantStore()

const waveStateClass = computed(() => {
  switch (assistantStore.assistantState) {
    case 'listening':
      return 'bg-green-400'
    case 'muted':
      return 'bg-blue-400'
    case 'error':
      return 'bg-red-400'
    case 'idle':
    default:
      return 'bg-gray-300'
  }
})

// переменная message для текстового поля
const message = ref('')

const messagesContainer = ref<HTMLElement | null>(null)

async function scrollToBottom() {
  await nextTick() // ждём, пока Vue обновит DOM
  const el = messagesContainer.value
  if (!el) return

  // ставим скролл в самый низ
  el.scrollTop = el.scrollHeight
}

const {
  messages,
  sendUserMessage,
  sendErrorMessage,     // пока можно не использовать, но он есть
  toggleMessage,
  collapseAll,
  onDeleteMessage,
  onCopyMessage,
  onRepeatMessage,
  addMessage,

} = useChat()



// функция отправки сообщения из текстового поля input
async function sendMessage() {
  const current = message.value
  message.value = ''  // очищаем поле сразу

  await sendUserMessage(current)
  await scrollToBottom()
}


</script>

<template>
  <div class="flex flex-col h-full max-h-screen">

    <!-- История сообщений -->
    <div ref="messagesContainer"
         class="flex-1 overflow-y-auto p-4 space-y-3 content-end"
         @dblclick.self="collapseAll">
      <ChatMessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        @toggle="toggleMessage(msg)"
        @delete="onDeleteMessage(msg)"
        @copy="onCopyMessage(msg)"
        @repeat="onRepeatMessage(msg)"
      />
    </div>

    <!-- Поле ввода -->
    <ChatInput
      class=""
      v-model="message"
      placeholder="Напишите сообщение..."
      @send="sendMessage"
    />

    <ChatInfoPanel @collapseall="collapseAll"/>

  </div>
</template>

<style scoped>

</style>
