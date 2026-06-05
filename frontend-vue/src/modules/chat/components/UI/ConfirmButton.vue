<!-- ConfirmButton.vue -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

const props = defineProps<{
  label?: string                // обычный текст кнопки
  confirmLabel?: string         // текст при подтверждении
  timeout?: number              // задержка отката в мс (по умолчанию 2000)
  btnClass?: string             // классы для стилизации
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void          // подтвержденное действие
  (e: 'click'): void            // любой клик (если нужно отследить)
}>()

const isConfirming = ref(false)
let timer: number | null = null

function reset() {
  isConfirming.value = false
  timer = null
}

function onClick(event: MouseEvent) {
  event.stopPropagation()
  emit('click')

  if (props.disabled) return

  // Первый клик — включаем подтверждение
  if (!isConfirming.value) {
    isConfirming.value = true
    timer = window.setTimeout(() => {
      reset()
    }, props.timeout ?? 2000)
    return
  }

  // Второй клик в режиме подтверждения
  if (timer !== null) {
    clearTimeout(timer)
  }
  reset()
  emit('confirm')
}

const text = computed(() =>
  isConfirming.value
    ? props.confirmLabel ?? 'Подтвердить?'
    : props.label ?? 'Кнопка'
)

onBeforeUnmount(() => {
  if (timer !== null) clearTimeout(timer)
})
</script>

<template>
  <button
    :class="btnClass"
    :disabled="disabled"
    @click="onClick"
  >
    <!-- Можно переопределить текст через слот, если захочешь -->
    <slot>
      {{ text }}
    </slot>
  </button>
</template>
