// src/composables/useChat.ts
import { ref } from 'vue'
import type { ChatMessage } from '@/types/chat.ts'
import { apiClient } from '@/modules/voice_assistant/api/apiClient.ts'
import { useAssistantStore } from '@/stores/assistantStore.ts'
import type { MessageType } from '@/types/chat.ts'

function makeTimestamp(): string {
  return new Date().toLocaleTimeString()
}

const messages = ref<ChatMessage[]>([])

const nextId = ref(messages.value.length + 1)
export function useChat() {




  function addMessage(text: string, type: MessageType): ChatMessage {
    const msg: ChatMessage = {
      id: nextId.value++,
      text,
      type,
      timestamp: makeTimestamp(),
      expanded: false,
    }

    messages.value.push(msg)
    return msg
  }

  function sendErrorMessage(err: unknown) {
    const messageText =
      err instanceof Error ? err.message : 'Неизвестная ошибка'

    addMessage('Ошибка отправки команды: ' + messageText, 'error')
  }

  function toggleMessage(msg: ChatMessage) {
    msg.expanded = !msg.expanded
  }

  function collapseAll() {
    messages.value.forEach((msg) => {
      msg.expanded = false
    })
  }

  function onDeleteMessage(msg: ChatMessage) {
    messages.value = messages.value.filter((m) => m.id !== msg.id)
  }

  async function onCopyMessage(msg: ChatMessage) {
    try {
      await navigator.clipboard.writeText(msg.text)
      console.log('Скопировано:', msg.text)
    } catch (err) {
      console.error('Ошибка копирования', err)
    }
  }

  async function onRepeatMessage(msg: ChatMessage) {
    // Повторная отправка сообщения как пользовательской команды.
    await sendUserMessage(msg.text)
  }



  // Работа с API
  async function sendUserMessage(text: string) {
    const trimmed = text.trim()
    if (!trimmed) return

    // Показываем в чате отправленную команду пользователя.
    addMessage(trimmed, 'user')

    try {
      // 2) шлём команду ассистенту
      const response = await apiClient.sendTextCommand(trimmed)

      // 3) показываем ответ ассистента мб асинхронности надо добавить
      addMessage(response.message, 'assistant')
    } catch (err) {
      console.error('Ошибка при отправке команды', err)
      sendErrorMessage(err)
    }
  }



  return {
    messages,
    sendUserMessage,
    sendErrorMessage,
    toggleMessage,
    collapseAll,
    onDeleteMessage,
    onCopyMessage,
    onRepeatMessage,
    addMessage,

  }
}
