<script setup>
import { computed, ref } from 'vue'
import { Rocket, TriangleAlert } from '@lucide/vue'
import { finalizeProject } from '@/services/api'
import ProgressRing from '@/components/ui/ProgressRing.vue'

const props = defineProps({
  project: { type: Object, required: true },
  // When true, shows a labelled "Finalize" button (used on the detail page).
  labeled: { type: Boolean, default: false },
})

const submitting = ref(false)
const localError = ref(null)
const showError = ref(false)

const error = computed(() => localError.value || props.project.finalizeError || null)
const completed = computed(() => props.project.completionPercentage === 100)
const finished = computed(() => Boolean(props.project.finalRepoUrl))
const inProgress = computed(
  () => props.project.finalizationPercentage > 0 || finished.value,
)
const eligible = computed(
  () =>
    completed.value &&
    props.project.finalizationPercentage === 0 &&
    !finished.value,
)

async function trigger() {
  if (submitting.value) return
  submitting.value = true
  localError.value = null
  showError.value = false
  try {
    await finalizeProject(props.project.executionId)
  } catch (e) {
    localError.value = e instanceof Error ? e.message : 'Finalization failed.'
    showError.value = true
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="relative inline-flex items-center gap-1">
    <!-- In progress / done: orange ring -->
    <ProgressRing
      v-if="inProgress"
      :value="project.finalizationPercentage"
      :size="labeled ? 52 : 40"
      :stroke="labeled ? 5 : 4"
      tone="warning"
    />

    <!-- Eligible: optional error warning + rocket -->
    <template v-else-if="eligible">
      <button
        v-if="error"
        type="button"
        class="inline-flex h-8 w-8 items-center justify-center rounded-full text-red-400 transition-colors hover:text-red-300"
        aria-label="Show finalization error"
        @click.stop="showError = !showError"
        @mouseenter="showError = true"
        @mouseleave="showError = false"
      >
        <TriangleAlert :size="18" />
      </button>

      <button
        type="button"
        class="inline-flex items-center justify-center gap-2 rounded-app border border-white/10 bg-brand-surface/60 font-semibold text-brand-textMuted transition-colors hover:text-brand-textMain disabled:opacity-50"
        :class="labeled ? 'min-h-[44px] px-3 text-xs' : 'h-9 w-9'"
        :disabled="submitting"
        :aria-label="`Finalize project ${project.name}`"
        @click.stop="trigger"
      >
        <Rocket :size="labeled ? 15 : 18" :class="submitting ? 'animate-bounce' : ''" />
        <span v-if="labeled">{{ submitting ? 'Finalizing…' : 'Finalize' }}</span>
      </button>

      <div
        v-if="showError && error"
        class="absolute right-0 top-11 z-20 w-56 rounded-app-sm border border-white/10 bg-brand-surface p-3 text-left text-xs text-brand-textMain shadow-lg"
        role="alert"
      >
        {{ error }}
      </div>
    </template>

    <!-- Not complete: disabled placeholder (dashboard only) -->
    <span
      v-else-if="!labeled"
      class="text-brand-textMuted/40"
      aria-label="Finalization unavailable"
    >
      —
    </span>
  </div>
</template>
