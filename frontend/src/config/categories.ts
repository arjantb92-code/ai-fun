/**
 * Centralized category configuration for transactions.
 * Single source of truth - used by TransactionCard, TransactionModal, and store.
 */

export const CATEGORIES = {
  boodschappen: {
    key: 'boodschappen',
    label: 'Boodschappen',
    icon: '🛒',
    color: '#71717a'
  },
  huishoudelijk: {
    key: 'huishoudelijk',
    label: 'Huishoudelijk',
    icon: '🏠',
    color: '#f59e0b'
  },
  winkelen: {
    key: 'winkelen',
    label: 'Winkelen',
    icon: '🛍️',
    color: '#ec4899'
  },
  vervoer: {
    key: 'vervoer',
    label: 'Vervoer',
    icon: '🚗',
    color: '#3b82f6'
  },
  reizen_vrije_tijd: {
    key: 'reizen_vrije_tijd',
    label: 'Reizen & Vrije Tijd',
    icon: '✈️',
    color: '#8b5cf6'
  },
  overig: {
    key: 'overig',
    label: 'Overig',
    icon: '📦',
    color: '#6b7280'
  }
} as const

type CategoryKey = keyof typeof CATEGORIES

export const getCategoryConfig = (key: string | null | undefined) =>
  (key ? CATEGORIES[key as CategoryKey] : null) ?? CATEGORIES.overig

export const getCategoryList = () => Object.values(CATEGORIES)

export const getCategoryLabel = (key: string) => getCategoryConfig(key).label

export const getCategoryIcon = (key: string) => getCategoryConfig(key).icon
