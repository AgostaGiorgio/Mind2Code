import { describe, expect, it } from 'vitest'

import {
  CURRENCY,
  LOCALE,
  formatDate,
  formatMoney,
  formatMoneySigned,
  formatNumber,
  formatPct,
  toNumber,
} from '@/utils/format'

describe('toNumber', () => {
  it('parses numeric values and rejects empty/invalid ones', () => {
    expect(toNumber('42')).toBe(42)
    expect(toNumber(3.5)).toBe(3.5)
    expect(toNumber(null)).toBeNull()
    expect(toNumber(undefined)).toBeNull()
    expect(toNumber('')).toBeNull()
    expect(toNumber('abc')).toBeNull()
  })
})

describe('formatMoney', () => {
  it('formats values and uses an em dash for invalid input', () => {
    expect(formatMoney(1234.5)).toBe(`${CURRENCY} 1,234.50`)
    expect(formatMoney(0)).toBe(`${CURRENCY} 0.00`)
    expect(formatMoney(null)).toBe('—')
  })
})

describe('formatMoneySigned', () => {
  it('prefixes positive and negative signs', () => {
    expect(formatMoneySigned(12.3)).toBe(`+${CURRENCY} 12.30`)
    expect(formatMoneySigned(-12.3)).toBe(`−${CURRENCY} 12.30`)
    expect(formatMoneySigned(0)).toBe(`${CURRENCY} 0.00`)
    expect(formatMoneySigned('x')).toBe('—')
  })
})

describe('formatNumber', () => {
  it('formats with locale separators', () => {
    expect(formatNumber(1234567.891)).toBe('1,234,567.89')
    expect(formatNumber('')).toBe('—')
  })
})

describe('formatPct', () => {
  it('formats percentages with an explicit sign', () => {
    expect(formatPct(12.345, 2)).toBe('+12.35%')
    expect(formatPct(-5, 0)).toBe('-5%')
    expect(formatPct(0, 1)).toBe('0.0%')
    expect(formatPct('nope')).toBe('—')
  })
})

describe('formatDate', () => {
  it('formats ISO dates and rejects invalid input', () => {
    expect(formatDate('2024-03-05T10:00:00Z')).toMatch(/\d{2}\/\d{2}\/2024/)
    expect(formatDate('not-a-date')).toBe('—')
    expect(formatDate(null)).toBe('—')
  })
})

describe('constants', () => {
  it('exposes the configured locale and currency', () => {
    expect(LOCALE).toBe('en-US')
    expect(CURRENCY).toBe('€')
  })
})
