import { describe, expect, it } from 'vitest'
import { TrendingDown, TrendingUp } from '@lucide/vue'

import { trendClass, trendIcon } from '@/utils/trend'

describe('trendClass', () => {
  it('is green for gains, red for losses and neutral otherwise', () => {
    expect(trendClass(10)).toBe('text-emerald-400')
    expect(trendClass(-10)).toBe('text-red-400')
    expect(trendClass(0)).toBe('text-brand-textMuted')
    expect(trendClass(null)).toBe('text-brand-textMuted')
    expect(trendClass('abc')).toBe('text-brand-textMuted')
  })
})

describe('trendIcon', () => {
  it('returns the matching icon or null when neutral', () => {
    expect(trendIcon(5)).toBe(TrendingUp)
    expect(trendIcon(-5)).toBe(TrendingDown)
    expect(trendIcon(0)).toBeNull()
    expect(trendIcon(undefined)).toBeNull()
  })
})
