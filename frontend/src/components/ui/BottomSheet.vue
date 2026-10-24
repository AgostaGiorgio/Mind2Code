<script setup>
import { X } from '@lucide/vue'

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
})

const emit = defineEmits(['close'])

const close = () => emit('close')
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet" appear>
      <div v-if="open" class="fixed inset-0 z-[100] flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="close" />

        <div
          class="sheet-panel relative w-full max-h-[90vh] bg-brand-background rounded-t-app shadow-app flex flex-col border-t border-white/10"
        >
          <div class="w-12 h-1.5 bg-white/20 rounded-full mx-auto mt-3 mb-2 shrink-0" />

          <div class="flex items-center justify-between gap-3 px-5 pb-4 pt-1 border-b border-white/5 shrink-0">
            <h2 class="text-brand-textMain font-bold text-lg truncate">{{ title }}</h2>
            <button
              type="button"
              @click="close"
              class="w-9 h-9 rounded-full flex items-center justify-center text-brand-textMuted bg-brand-surface/50 hover:text-brand-textMain transition-colors shrink-0"
            >
              <X :size="18" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-5 py-5 hide-scrollbar">
            <slot />
          </div>

          <div
            v-if="$slots.footer"
            class="px-5 pt-4 border-t border-white/5 shrink-0"
            style="padding-bottom: calc(1.25rem + env(safe-area-inset-bottom))"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
