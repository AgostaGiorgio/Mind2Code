// Shared formatting helpers. Adjust LOCALE / CURRENCY to the app's domain; the
// numbers stay in the chosen locale regardless of the UI language.

export const LOCALE = 'en-US'
export const CURRENCY = '€'

export function formatMoney(value, decimals = 2) {
  const n = toNumber(value)
  if (n === null) return '—'
  return (
    CURRENCY + ' ' + n.toLocaleString(LOCALE, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  )
}

export function formatMoneySigned(value, decimals = 2) {
  const n = toNumber(value)
  if (n === null) return '—'
  const sign = n > 0 ? '+' : n < 0 ? '−' : ''
  return `${sign}${CURRENCY} ${Math.abs(n).toLocaleString(LOCALE, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`
}

export function formatNumber(value, decimals = 2) {
  const n = toNumber(value)
  if (n === null) return '—'
  return n.toLocaleString(LOCALE, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export function formatPct(value, decimals = 2) {
  const n = toNumber(value)
  if (n === null) return '—'
  const sign = n > 0 ? '+' : ''
  return sign + n.toFixed(decimals) + '%'
}

export function formatDate(value) {
  const d = toDate(value)
  if (!d) return '—'
  return d.toLocaleDateString(LOCALE, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function toNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isNaN(n) ? null : n
}

function toDate(value) {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}
