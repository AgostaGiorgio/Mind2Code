import { TrendingUp, TrendingDown } from '@lucide/vue'

// Color class for a trend/P&L value: positive green, negative red,
// zero (or unavailable) neutral.
export function trendClass(value) {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return 'text-brand-textMuted'
  return n > 0 ? 'text-emerald-400' : 'text-red-400'
}

// Icon for a trend/P&L value: null when neutral (zero/absent).
export function trendIcon(value) {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return null
  return n > 0 ? TrendingUp : TrendingDown
}
