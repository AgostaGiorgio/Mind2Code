<script setup>
import AppHeader from '@/components/AppHeader.vue'
import AppNavbar from '@/components/AppNavbar.vue'
import ToastHost from '@/components/ui/ToastHost.vue'
</script>

<template>
  <div
    class="min-h-screen bg-brand-background flex flex-col items-center text-brand-textMain font-sans pb-[calc(6rem_+_env(safe-area-inset-bottom))] lg:pb-8 selection:bg-brand-primary selection:text-white"
  >
    <AppHeader />

    <div class="flex w-full flex-1 flex-col lg:pl-28">
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </div>

    <AppNavbar />
    <ToastHost />
  </div>
</template>
