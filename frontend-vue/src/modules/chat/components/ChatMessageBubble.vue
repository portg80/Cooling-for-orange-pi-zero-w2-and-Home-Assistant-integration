<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import ChatMessageActions from '@/modules/chat/components/ChatMessageActions.vue'

import type { ChatMessage, MessageType } from '@/types/chat.ts'

const props = defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'delete'): void
  (e: 'copy'): void
  (e: 'repeat'): void
}>()

function onClick() {
  emit('toggle')
}

function bubbleClass(message: ChatMessage) {
  if (message.type === 'user') {
    return 'bg-blue-300/10  border-blue-300/30 border-2 justify-self-end'
  }
  if (message.type === 'assistant') {
    return 'bg-zinc-800/100 border-zinc-400/30 border-2 text-white '
  }
  if (message.type === 'error') {
    return 'bg-red-600/20 border-red-400/70 border-2 text-white '
  }
  // всё остальное считаем "info"
  return 'bg-green-800/20 border-green-500/70 border-2 '
}
</script>

<template>
  <div
    class="message-bubble hover:scale-103 min-w-4/12 p-4 px-5 rounded-2xl text-2xl w-fit cursor-pointer"
    :class="bubbleClass(message)"
    @click="onClick"
  >
    <div class="flex justify-between gap-3">
      <div class="whitespace-pre-wrap">
        {{ message.text }}
      </div>
      <div class="text-xs text-gray-100/50 mt-1">
        {{ message.timestamp }}
      </div>
    </div>

    <ChatMessageActions
      v-if="message.expanded"
      :messageType="message.type"
      @delete="emit('delete')"
      @copy="emit('copy')"
      @repeat="emit('repeat')"
    />
  </div>
</template>

<style scoped></style>
