// src/composables/useVoiceAssistantControl.ts
import { ref } from 'vue'
import { apiClient } from '@/modules/voice_assistant/api/apiClient.ts'
import type {
  ActivateResponse,
  CancelResponse,
  AssistantStatusResponse,
  ToggleWakewordResponse,
} from '@/modules/voice_assistant/api/apiClient.ts'
import { useAssistantStore } from '@/stores/assistantStore.ts'

export function useVoiceAssistantControl() {
  const assistantStore = useAssistantStore()

  const isLoading = ref(false)
  const lastMessage = ref<string | null>(null)
  const lastError = ref<string | null>(null)
  const lastStatus = ref<AssistantStatusResponse | null>(null)

  // === АКТИВАЦИЯ ЧЕРЕЗ STORE ===
  async function activateAssistant(): Promise<ActivateResponse | void> {
    isLoading.value = true
    lastError.value = null

    try {
      const data = await assistantStore.activateListening()
      lastMessage.value = data.message

      if (data.status === 'error') {
        lastError.value = data.message
      }

      return data
    } catch (e: any) {
      console.error('[useAssistantControl] activate error', e)
      lastError.value = e?.message ?? 'Ошибка активации ассистента'
    } finally {
      isLoading.value = false
    }
  }

  // === ОТМЕНА ЧЕРЕЗ STORE ===
  async function cancelListening(): Promise<CancelResponse | void> {
    isLoading.value = true
    lastError.value = null

    try {
      const data = await apiClient.toggleWakeword()
      lastMessage.value = data.message

      if (data.status === 'error') {
        lastError.value = data.message
      }

      return data
    } catch (e: any) {
      console.error('[useAssistantControl] cancel error', e)
      lastError.value = e?.message ?? 'Ошибка отмены команды'
    } finally {
      isLoading.value = false
    }
  }

  // Статус
  async function fetchStatus(): Promise<AssistantStatusResponse | void> {
    try {
      const data = await apiClient.getStatus()
      lastStatus.value = data
      // при желании можешь сюда добавить assistantStore.applyAssistantStatus(data)
      return data
    } catch (e: any) {
      console.error('[useAssistantControl] status error', e)
      lastError.value = e?.message ?? 'Ошибка получения статуса'
    }
  }


  async function toggleWakeword(): Promise<ToggleWakewordResponse | void> {
    isLoading.value = true
    lastError.value = null

    try {
      const data = await apiClient.toggleWakeword()
      if (!data) return

      lastMessage.value = data.message

      if (data.status === 'error') {
        lastError.value = data.message
      }

      return data
    } catch (e: any) {
      console.error('[useAssistantControl] toggle wakeword error', e)
      lastError.value = e?.message ?? 'Ошибка переключения wakeword'
    } finally {
      isLoading.value = false
    }
  }

  return {
    // state
    isLoading,
    lastMessage,
    lastError,
    lastStatus,
    // actions
    activateAssistant,
    cancelListening,
    fetchStatus,
    toggleWakeword,
  }
}
