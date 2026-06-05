<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'

const props = defineProps<{
  label?: string          // обычный текст кнопки
  successLabel?: string   // текст после успешного действия
  timeout?: number        // задержка отката, мс (по умолчанию 2000)
  btnClass?: string       // классы для стилизации
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'click'): void      // событие "действие выполнено"
}>()

const isSuccess = ref(false)
let timer: number | null = null

function reset() {
  isSuccess.value = false
  timer = null
}

function onClick(event: MouseEvent) {
  event.stopPropagation()
  if (props.disabled) return

  // сообщаем наружу: "кнопка нажата, делай своё действие" (например, копирование)
  emit('click')

  // переключаемся в режим "успех"
  isSuccess.value = true

  // если был старый таймер — сбросим
  if (timer !== null) {
    clearTimeout(timer)
  }

  // через timeout вернём текст обратно
  timer = window.setTimeout(() => {
    reset()
  }, props.timeout ?? 2000)
}

const text = computed(() =>
  isSuccess.value
    ? props.successLabel ?? 'Готово'
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
    <slot>
      {{ text }}
    </slot>
  </button>
</template>
