<script setup>
import { computed, ref, watch } from 'vue'
import { Rocket, TriangleAlert } from '@lucide/vue'
import { startProjectPhase } from '@/services/api'
import ProgressRing from '@/components/ui/ProgressRing.vue'

const props = defineProps({
  project: { type: Object, required: true },
})

const submitting = ref(false)
const requested = ref(false)
const localError = ref(null)
const showError = ref(false)

const error = computed(() => localError.value || props.project.finalizeError || null)
const finished = computed(
  () =>
    Boolean(props.project.finalRepoUrl) ||
    props.project.status === 'RETROSPECTIVE_DONE',
)
const inProgress = computed(
  () =>
    !finished.value &&
    (props.project.status === 'RETROSPECTIVE_RUNNING' ||
      props.project.finalizationPercentage > 0),
)
const canStart = computed(
  () => props.project.status === 'REVIEW_DONE',
)
const eligible = computed(
  () => canStart.value && !inProgress.value && !finished.value,
)
const ringValue = computed(() =>
  finished.value ? 100 : props.project.finalizationPercentage,
)

watch(
  () => [props.project.status, props.project.finalizationPercentage],
  () => {
    requested.value = false
  },
)

async function trigger() {
  if (submitting.value || requested.value) return
  submitting.value = true
  localError.value = null
  showError.value = false
  try {
    await startProjectPhase(props.project.id, 'RETROSPECTIVE')
    requested.value = true
  } catch (e) {
    localError.value = e instanceof Error ? e.message : 'Could not start the retrospective.'
    showError.value = true
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="relative inline-flex items-center gap-1">
    <!-- Retrospective running / finished: orange ring -->
    <ProgressRing
      v-if="inProgress || finished"
      :value="ringValue"
      :size="40"
      :stroke="4"
      tone="warning"
    />

    <template v-else-if="eligible">
      <button
        v-if="error"
        type="button"
        class="inline-flex h-8 w-8 items-center justify-center rounded-full text-red-400 transition-colors hover:text-red-300"
        aria-label="Show retrospective error"
        @click.stop="showError = !showError"
        @mouseenter="showError = true"
        @mouseleave="showError = false"
      >
        <TriangleAlert :size="18" />
      </button>

      <button
        type="button"
        class="inline-flex h-9 w-9 items-center justify-center rounded-app border border-white/10 bg-brand-surface/60 font-semibold text-brand-textMuted transition-colors hover:text-brand-textMain disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="submitting || requested"
        :aria-label="`Start retrospective phase for ${project.name}`"
        @click.stop="trigger"
      >
        <Rocket :size="18" :class="submitting ? 'animate-bounce' : ''" />
      </button>

      <div
        v-if="showError && error"
        class="absolute right-0 top-11 z-20 w-56 rounded-app-sm border border-white/10 bg-brand-surface p-3 text-left text-xs text-brand-textMain shadow-lg"
        role="alert"
      >
        {{ error }}
      </div>
    </template>

    <span v-else class="text-brand-textMuted/40" aria-label="Retrospective unavailable">
      —
    </span>
  </div>
</template>
