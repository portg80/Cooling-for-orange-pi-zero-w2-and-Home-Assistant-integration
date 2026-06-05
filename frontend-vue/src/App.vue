<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-100 text-gray-900">
    <nav class="p-4 bg-white shadow">
      <RouterLink to="/" class="mr-4">Home</RouterLink>
    </nav>

    <main class="">
      <RouterView />
    </main>

  </div>

</template>

<style scoped>

</style>
