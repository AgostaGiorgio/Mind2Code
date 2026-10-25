<script setup>
import { computed } from 'vue'

const props = defineProps({
  primaryValue: { type: Number, required: true },
  // When null the inner (finalization) arc is not rendered.
  secondaryValue: { type: Number, default: null },
  size: { type: Number, default: 52 },
  stroke: { type: Number, default: 5 },
  secondaryStroke: { type: Number, default: 4 },
  gap: { type: Number, default: 2 },
  // 'brand' (violet) or 'warning' (orange).
  primaryTone: { type: String, default: 'brand' },
  secondaryTone: { type: String, default: 'warning' },
})

function clamp(value) {
  return Math.min(100, Math.max(0, value))
}

const primary = computed(() => clamp(props.primaryValue))
const secondary = computed(() =>
  props.secondaryValue === null ? null : clamp(props.secondaryValue),
)

const center = computed(() => props.size / 2)

const outerRadius = computed(() => (props.size - props.stroke) / 2)
const innerRadius = computed(
  () => outerRadius.value - props.stroke / 2 - props.gap - props.secondaryStroke / 2,
)

const outerCircumference = computed(() => 2 * Math.PI * outerRadius.value)
const innerCircumference = computed(() => 2 * Math.PI * innerRadius.value)

const outerOffset = computed(() => outerCircumference.value * (1 - primary.value / 100))
const innerOffset = computed(
  () => innerCircumference.value * (1 - (secondary.value ?? 0) / 100),
)

const primaryClass = computed(() =>
  props.primaryTone === 'warning' ? 'text-amber-400' : 'text-brand-primary',
)
const secondaryClass = computed(() =>
  props.secondaryTone === 'warning' ? 'text-amber-400' : 'text-brand-primary',
)

const ariaLabel = computed(() =>
  secondary.value === null
    ? `${primary.value}% complete`
    : `${primary.value}% complete, ${secondary.value}% finalized`,
)
</script>

<template>
  <div
    class="relative inline-flex shrink-0 items-center justify-center"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="img"
    :aria-label="ariaLabel"
  >
    <svg :width="size" :height="size" class="-rotate-90" aria-hidden="true">
      <!-- Outer track + completion arc -->
      <circle
        :cx="center"
        :cy="center"
        :r="outerRadius"
        fill="none"
        stroke="currentColor"
        :stroke-width="stroke"
        class="text-white/10"
      />
      <circle
        :cx="center"
        :cy="center"
        :r="outerRadius"
        fill="none"
        stroke="currentColor"
        :stroke-width="stroke"
        stroke-linecap="round"
        class="transition-[stroke-dashoffset] duration-300 ease-out"
        :class="primaryClass"
        :stroke-dasharray="outerCircumference"
        :stroke-dashoffset="outerOffset"
      />

      <!-- Inner track + finalization arc -->
      <template v-if="secondary !== null">
        <circle
          :cx="center"
          :cy="center"
          :r="innerRadius"
          fill="none"
          stroke="currentColor"
          :stroke-width="secondaryStroke"
          class="text-white/10"
        />
        <circle
          :cx="center"
          :cy="center"
          :r="innerRadius"
          fill="none"
          stroke="currentColor"
          :stroke-width="secondaryStroke"
          stroke-linecap="round"
          class="transition-[stroke-dashoffset] duration-300 ease-out"
          :class="secondaryClass"
          :stroke-dasharray="innerCircumference"
          :stroke-dashoffset="innerOffset"
        />
      </template>
    </svg>
  </div>
</template>
