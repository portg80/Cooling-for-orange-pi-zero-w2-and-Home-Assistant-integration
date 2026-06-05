// src/stores/assistantStore.ts
import { defineStore } from 'pinia'
import { apiClient } from '@/modules/voice_assistant/api/apiClient.ts'
import type {
  AssistantStatusResponse,
  WakewordStatusResponse,
  ToggleWakewordResponse,
  AssistantServerState,
} from '@/modules/voice_assistant/api/apiClient.ts'

// Состояние для UI (агрегированное)
export type AssistantState = 'idle' | 'listening' | 'muted' | 'cancelling' | 'error'

export const useAssistantStore = defineStore('assistant', {
  state: () => ({
    // --- сырой серверный статус Vosk ---
    voskState: 'IDLE' as AssistantServerState | string,

    // --- wakeword ---
    wakewordPaused: false,
    wakewordActive: false,
    wakewordManualMute: false,

    // последняя инфа от сервера (могут пригодиться)
    lastStatusAt: null as number | null,
  }),

  actions: {

  },
})
