<script setup>
import { CheckCircle2, AlertCircle, Info } from '@lucide/vue'
import { useToast } from '@/composables/useToast'

const { toasts } = useToast()

const iconFor = (type) => (type === 'success' ? CheckCircle2 : type === 'error' ? AlertCircle : Info)
const colorFor = (type) =>
  type === 'success' ? 'text-emerald-400' : type === 'error' ? 'text-red-400' : 'text-brand-primary'
</script>

<template>
  <div
    class="fixed top-0 left-0 right-0 z-[200] flex flex-col items-center gap-2 px-4 pointer-events-none"
    style="padding-top: calc(0.75rem + env(safe-area-inset-top))"
  >
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto w-full max-w-sm bg-brand-surface/95 backdrop-blur-xl border border-white/10 rounded-app-sm shadow-app px-4 py-3 flex items-center gap-3"
      >
        <component :is="iconFor(t.type)" :size="18" class="shrink-0" :class="colorFor(t.type)" />
        <span class="text-brand-textMain text-sm">{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
