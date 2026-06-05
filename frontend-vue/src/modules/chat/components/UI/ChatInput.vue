<script setup lang="ts">
  import { defineProps, defineEmits } from 'vue'
  import NotifyButton from '@/modules/chat/components/UI/NotifyButton.vue'

  const props = defineProps<{
    modelValue: string
    placeholder?: string
  }>()

  const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void
    (e: 'send'): void
  }>()

  function onKeyupEnter(){
    emit('send')
  }

  function onInput(e: Event) {
    const target = e.target as HTMLInputElement
    emit('update:modelValue', target.value)
  }

</script>

<template>
  <!-- Поле ввода -->
  <div class="flex h-12 bg-gray-500/30 rounded-2xl ">

    <input
      :value="modelValue"
      @input="onInput"
      @keyup.enter="onKeyupEnter"
      class="flex-1 h-full px-4 rounded-2xl rounded-r-none text-gray-100 focus:outline-none focus:bg-gray-500/10"
      :placeholder="placeholder ?? 'Напишите сообщение...'"
    />
    <NotifyButton
      :btnClass="'px-5  py-1 text-sm rounded-2xl rounded-l-none bg-gray-500/40 hover:bg-gray-500/60'"
      label="Отправить"
      successLabel="Отправлено"
      :timeout="700"
      @click="emit('send')"
    />
  </div>
</template>

<style scoped>

</style>
