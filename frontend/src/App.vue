<script setup>
import AppHeader from '@/components/AppHeader.vue'
import ToastHost from '@/components/ui/ToastHost.vue'
import { useSse } from '@/composables/useSse'
import { useProjectsStore } from '@/stores/projects'

const store = useProjectsStore()
const { status } = useSse(store.applyProgressEvent, store.applyFinalizationEvent)
</script>

<template>
  <div
    class="min-h-screen bg-brand-background flex flex-col items-center text-brand-textMain font-sans pb-[calc(2rem_+_env(safe-area-inset-bottom))] selection:bg-brand-primary selection:text-white"
  >
    <AppHeader :status="status" />

    <div class="flex w-full flex-1 flex-col">
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </div>

    <ToastHost />
  </div>
</template>
