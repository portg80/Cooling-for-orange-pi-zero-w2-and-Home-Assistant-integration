<script setup lang="ts">
import Chat from '@/modules/chat/Chat.vue'
import VoiceAssistantControls from '@/modules/voice_assistant/VoiceAssistantControls.vue'

</script>

<template>
  <div class="min-h-screen bg-zinc-900 text-white p-6">
    <div class="mx-auto max-w-7xl flex flex-col gap-8 lg:flex-row lg:items-start">
      <!-- Слева -->
      <div class="lg:w-7/12 self-center">
        <h1 class="text-2xl font-bold mb-4">Афина</h1>

        <VoiceAssistantControls />
      </div>

      <!-- Справа -->
      <div class="lg:w-13/12">
        <div class="h-[700px] max-h-[70vh]
        overflow-y-auto rounded-xl border border-zinc-700/70 bg-zinc-800/40 px-4 py-2">
          <Chat />
        </div>
      </div>
    </div>
  </div>
</template>
