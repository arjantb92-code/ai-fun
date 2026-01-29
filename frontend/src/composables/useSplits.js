import { ref, computed } from 'vue'

/**
 * Composable for managing transaction splits (who pays/shares what).
 * Handles user inclusion, weight management, and provides reactive state.
 * 
 * @param {Array} initialSplits - Initial splits array [{user_id, weight}]
 * @returns {Object} Split management functions and state
 */
export function useSplits(initialSplits = []) {
  const splits = ref([...initialSplits])

  /**
   * Toggle user inclusion in split
   * @param {number} userId - User ID to toggle
   */
  const toggleUser = (userId) => {
    const idx = splits.value.findIndex(s => s.user_id === userId)
    if (idx !== -1) {
      splits.value.splice(idx, 1)
    } else {
      splits.value.push({ user_id: userId, weight: 1 })
    }
    // Force reactivity update
    splits.value = [...splits.value]
  }

  /**
   * Increment weight for a user
   * @param {number} userId - User ID
   */
  const incrementWeight = (userId) => {
    const split = splits.value.find(s => s.user_id === userId)
    if (split) {
      split.weight++
      splits.value = [...splits.value]
    }
  }

  /**
   * Decrement weight for a user (minimum 1)
   * @param {number} userId - User ID
   */
  const decrementWeight = (userId) => {
    const split = splits.value.find(s => s.user_id === userId)
    if (split && split.weight > 1) {
      split.weight--
      splits.value = [...splits.value]
    }
  }

  /**
   * Check if user is included in splits
   * @param {number} userId - User ID
   * @returns {boolean}
   */
  const isUserIncluded = (userId) => splits.value.some(s => s.user_id === userId)

  /**
   * Get weight for a user
   * @param {number} userId - User ID
   * @returns {number} Weight or 0 if not included
   */
  const getWeight = (userId) => splits.value.find(s => s.user_id === userId)?.weight ?? 0

  /**
   * Reset splits to new array
   * @param {Array} newSplits - New splits array
   */
  const reset = (newSplits = []) => {
    splits.value = [...newSplits]
  }

  /**
   * Initialize splits from group members (all included with weight 1)
   * @param {Array} members - Array of user objects with id property
   */
  const initFromMembers = (members) => {
    splits.value = members.map(m => ({ user_id: m.id, weight: 1 }))
  }

  // Computed
  const totalWeight = computed(() => 
    splits.value.reduce((sum, s) => sum + s.weight, 0)
  )

  const includedUserIds = computed(() => 
    splits.value.map(s => s.user_id)
  )

  return {
    splits,
    toggleUser,
    incrementWeight,
    decrementWeight,
    isUserIncluded,
    getWeight,
    reset,
    initFromMembers,
    totalWeight,
    includedUserIds
  }
}
