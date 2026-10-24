<script setup>
import { isSafeGitHubUrl } from '@/utils/github'

defineProps({
  url: { type: String, default: '' },
  // Accessible label; defaults to a generic one.
  label: { type: String, default: 'Open GitHub repository' },
})
</script>

<template>
  <a
    v-if="isSafeGitHubUrl(url)"
    :href="url"
    target="_blank"
    rel="noopener noreferrer"
    class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/5 bg-brand-surface/60 text-brand-textMuted transition-colors hover:text-brand-textMain"
    :aria-label="label"
  >
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
      <path
        d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.27-1.68-1.27-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.69 1.24 3.34.95.1-.74.4-1.24.72-1.53-2.55-.29-5.24-1.28-5.24-5.68 0-1.25.45-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.18a10.9 10.9 0 0 1 2.87-.39c.98 0 1.96.13 2.87.39 2.18-1.49 3.14-1.18 3.14-1.18.63 1.59.23 2.76.11 3.05.74.8 1.18 1.83 1.18 3.08 0 4.41-2.69 5.39-5.25 5.67.41.36.78 1.06.78 2.14 0 1.54-.01 2.79-.01 3.17 0 .31.21.68.8.56A11.51 11.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5z"
      />
    </svg>
  </a>
</template>
