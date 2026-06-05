<script setup lang="ts">
  import { defineEmits, defineProps, ref } from 'vue'
  import ConfirmButton from '@/modules/chat/components/UI/ConfirmButton.vue'
  import NotifyButton from '@/modules/chat/components/UI/NotifyButton.vue'

  const props = defineProps<{
      messageType: string
    }
  >()

  const emit = defineEmits<{
    (e: 'copy'): void
    (e: 'delete'): void
    (e: 'repeat'): void
  }>()

</script>

<template>
  <div class="flex justify-end mt-2 text-black">
    <ConfirmButton
      v-if="messageType=='user'"
      :label="'⟲ Повторить'"
      confirm-label="Подтвердить?"
      :timeout="2000"
      btn-class="px-2 py-1 mx-1 text-sm rounded text-gray-100 bg-orange-400/20 border border-yellow-400/40 hover:bg-orange-400/30"
      @confirm="emit('repeat')"
    />

    <NotifyButton
      :btnClass="'px-2 py-1 mx-1 text-sm rounded text-gray-100 bg-green-300/20 border border-green-300/40 hover:bg-green-400/30'"
      label="⧉ Копировать"
      successLabel="Скопировано!"
      :timeout="2000"
      @click="emit('copy')"
    />

    <ConfirmButton
      :label="'Удалить'"
      confirm-label="Подтвердить?"
      :timeout="2000"
      btn-class="px-4 py-1 mx-2 ml-5 text-sm rounded text-gray-100 bg-red-500/50 border-2 border-red-500/50 hover:bg-red-600/80 hover:border-gray-100/70"
      @confirm="emit('delete')"
    />
  </div>
</template>

<style scoped>

</style>
