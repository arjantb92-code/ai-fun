import { ref, computed } from 'vue'

/**
 * Composable for managing multi-select state.
 * Used for bulk operations on transactions.
 * 
 * @returns {Object} Selection management functions and state
 */
export function useSelection() {
  const selected = ref(new Set())

  /**
   * Toggle selection for an item
   * @param {number|string} id - Item ID to toggle
   */
  const toggle = (id) => {
    const s = new Set(selected.value)
    if (s.has(id)) {
      s.delete(id)
    } else {
      s.add(id)
    }
    selected.value = s
  }

  /**
   * Select all items from array
   * @param {Array} ids - Array of IDs to select
   */
  const selectAll = (ids) => {
    selected.value = new Set(ids)
  }

  /**
   * Clear all selections
   */
  const clear = () => {
    selected.value = new Set()
  }

  /**
   * Check if item is selected
   * @param {number|string} id - Item ID
   * @returns {boolean}
   */
  const isSelected = (id) => selected.value.has(id)

  /**
   * Get array of selected IDs
   * @returns {Array}
   */
  const getSelectedArray = () => Array.from(selected.value)

  // Computed
  const count = computed(() => selected.value.size)
  const hasSelection = computed(() => selected.value.size > 0)

  return {
    selected,
    toggle,
    selectAll,
    clear,
    isSelected,
    getSelectedArray,
    count,
    hasSelection
  }
}
