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
}

/**
 * Get category configuration by key
 * @param {string} key - Category key
 * @returns {Object} Category config with key, label, icon, color
 */
export const getCategoryConfig = (key) => CATEGORIES[key] || CATEGORIES.overig

/**
 * Get all categories as an array
 * @returns {Array} Array of category objects
 */
export const getCategoryList = () => Object.values(CATEGORIES)

/**
 * Get category label by key
 * @param {string} key - Category key
 * @returns {string} Category label
 */
export const getCategoryLabel = (key) => getCategoryConfig(key).label

/**
 * Get category icon by key
 * @param {string} key - Category key
 * @returns {string} Category icon (emoji)
 */
export const getCategoryIcon = (key) => getCategoryConfig(key).icon
