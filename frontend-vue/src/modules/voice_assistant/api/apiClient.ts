// src/services/apiClient.ts

import axios from 'axios'

// базовый URL до твоего Flask-серверa
// Flask отдает /api/..., а дальше уже /voicecore/... или /avatar/...
const http = axios.create({
  baseURL: 'http://127.0.0.1:6789/api',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// возможные состояния движка Vosk (как ты их сам считаешь)
export type AssistantServerState = 'IDLE' | 'LISTENING' | 'CANCELLING' | 'MUTED'

/**
 * GET /api/voicecore/status-voice-engine
 * {
 *   state_assistant_vosk: "...",
 *   wakeword_paused: boolean
 * }
 */
export type AssistantStatusResponse = {
  state_assistant_vosk: AssistantServerState | string
  wakeword_paused: boolean
}

/**
 * POST /api/voicecore/assistant/activate-listening-command
 * { status: 'activated' | 'error', message: string }
 */
export type ActivateResponse = {
  status: 'activated' | 'error'
  message: string
}

/**
 * POST /api/voicecore/assistant/cancel-listening-command
 * { status: 'cancelled' | 'error', message: string }
 */
export type CancelResponse = {
  status: 'cancelled' | 'error'
  message: string
}

/**
 * POST /api/voicecore/assistant/send-text-command
 * { status: 'executed' | 'not_found' | 'error', message: string }
 */
export type SendTextResponse = {
  status: 'executed' | 'not_found' | 'error'
  message: string
}

/**
 * GET /api/voicecore/wakeword/status
 * структура произвольная, но точно могут быть wakeword_active / manual_mute
 */
export type WakewordStatusResponse = {
  wakeword_active?: boolean
  manual_mute?: boolean
  [key: string]: any
}

/**
 * POST /api/voicecore/wakeword/toggle-mute
 * Успех:
 * {
 *   status: 'success',
 *   message: string,
 *   state_assistant_vosk: string,
 *   wakeword_active: boolean,
 *   manual_mute: boolean
 * }
 * Ошибка: { status: 'error', message: string }
 */
export type ToggleWakewordResponse = {
  status: 'success' | 'error'
  message: string
  state_assistant_vosk?: AssistantServerState | string
  wakeword_active?: boolean
  manual_mute?: boolean
}

/**
 * POST /api/voicecore/wakeword/mute
 * Успех:
 * {
 *   status: 'success',
 *   message: 'Wakeword замучен',
 *   wakeword_state: 'muted'
 * }
 */
export type MuteWakewordResponse = {
  status: 'success' | 'error'
  message: string
  wakeword_state?: 'muted'
}

/**
 * POST /api/voicecore/wakeword/unmute
 * Успех:
 * {
 *   status: 'success',
 *   message: 'Wakeword включен',
 *   wakeword_state: 'listening'
 * }
 */
export type UnmuteWakewordResponse = {
  status: 'success' | 'error'
  message: string
  wakeword_state?: 'listening'
}

/**
 * POST /api/avatar/apply-skin
 * { status: 'success' | 'error', message: string, skin?: string }
 */
export type ApplySkinResponse = {
  status: 'success' | 'error'
  message: string
  skin?: string
}

/** ---------- Сам клиент ---------- **/

export const apiClient = {
  /**
   * Отправка текстовой команды:
   * POST /api/voicecore/assistant/send-text-command
   */
  async sendTextCommand(text: string): Promise<SendTextResponse> {
    console.log('[apiClient] POST /voicecore/assistant/send-text-command', text)
    const { data } = await http.post<SendTextResponse>(
      '/voicecore/assistant/send-text-command',
      { text }
    )
    console.log('[apiClient] response', data)
    return data
  },

  /**
   * Статус движка распознавания + пауза wakeword:
   * GET /api/voicecore/status-voice-engine
   */
  async getStatus(): Promise<AssistantStatusResponse> {
    const { data } = await http.get<AssistantStatusResponse>(
      '/voicecore/status-voice-engine'
    )
    return data
  },

  /**
   * Активировать прослушивание команды (байпас wakeword):
   * POST /api/voicecore/assistant/activate-listening-command
   */
  async activateAssistant(): Promise<ActivateResponse> {
    const { data } = await http.post<ActivateResponse>(
      '/voicecore/assistant/activate-listening-command'
    )
    return data
  },

  /**
   * Отменить прослушивание команды в Vosk:
   * POST /api/voicecore/assistant/cancel-listening-command
   */
  async cancelCommandAssistant(): Promise<CancelResponse> {
    const { data } = await http.post<CancelResponse>(
      '/voicecore/assistant/cancel-listening-command'
    )
    return data
  },

  /**
   * Статус wakeword:
   * GET /api/voicecore/wakeword/status
   */
  async getWakewordStatus(): Promise<WakewordStatusResponse> {
    const { data } = await http.get<WakewordStatusResponse>(
      '/voicecore/wakeword/status'
    )
    return data
  },

  /**
   * Тоггл mute/unmute wakeword:
   * POST /api/voicecore/wakeword/toggle-mute
   */
  async toggleWakeword(): Promise<ToggleWakewordResponse> {
    const { data } = await http.post<ToggleWakewordResponse>(
      '/voicecore/wakeword/toggle-mute'
    )
    return data
  },

  /**
   * Жёстко замутить wakeword:
   * POST /api/voicecore/wakeword/mute
   */
  async muteWakeword(): Promise<MuteWakewordResponse> {
    const { data } = await http.post<MuteWakewordResponse>(
      '/voicecore/wakeword/mute'
    )
    return data
  },

  /**
   * Размутить wakeword:
   * POST /api/voicecore/wakeword/unmute
   */
  async unmuteWakeword(): Promise<UnmuteWakewordResponse> {
    const { data } = await http.post<UnmuteWakewordResponse>(
      '/voicecore/wakeword/unmute'
    )
    return data
  },

  /**
   * Применить скин аватара:
   * POST /api/avatar/apply-skin
   */
  async applySkin(skin: string): Promise<ApplySkinResponse> {
    const { data } = await http.post<ApplySkinResponse>(
      '/avatar/apply-skin',
      { skin }
    )
    return data
  },
}
