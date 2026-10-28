<script setup>
defineProps({
  status: { type: String, default: 'connecting' },
})

const statusLabel = {
  connecting: 'Connecting',
  connected: 'Connected',
  reconnecting: 'Reconnecting',
  disconnected: 'Disconnected',
}

const statusClass = {
  connecting: 'bg-brand-secondary/20 text-brand-secondary',
  connected: 'bg-emerald-500/20 text-emerald-400',
  reconnecting: 'bg-amber-500/20 text-amber-400',
  disconnected: 'bg-red-500/20 text-red-400',
}
</script>

<template>
  <header
    class="mb-2 mt-8 flex w-full items-center justify-between gap-3 px-5"
  >
    <div class="text-2xl font-extrabold tracking-tighter cursor-default">
      <span class="text-brand-textMain">Mind</span><span class="text-brand-primary">2</span><span class="text-brand-textMain">Code</span>
    </div>

    <div
      class="flex shrink-0 items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold"
      :class="statusClass[status]"
      aria-live="polite"
      aria-atomic="true"
    >
      <span class="relative flex h-2 w-2">
        <span
          v-if="status !== 'connected'"
          class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
          :class="status === 'disconnected' ? 'bg-red-400' : 'bg-brand-secondary'"
        />
        <span
          class="relative inline-flex h-2 w-2 rounded-full"
          :class="
            status === 'connected'
              ? 'bg-emerald-400'
              : status === 'disconnected'
                ? 'bg-red-400'
                : 'bg-brand-secondary'
          "
        />
      </span>
      {{ statusLabel[status] }}
    </div>
  </header>
</template>
