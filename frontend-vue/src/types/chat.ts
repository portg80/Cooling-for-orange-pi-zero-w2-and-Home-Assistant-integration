// src/types/chat.ts
//export — чтобы их можно было импортировать в других файлах.
export type MessageType = 'assistant' | 'user' | 'info' | 'error'

export type ChatMessage = {
  id: number
  text: string
  type: MessageType
  timestamp: string
  expanded?: boolean
}
