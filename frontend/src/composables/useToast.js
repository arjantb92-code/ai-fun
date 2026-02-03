import { ref, onUnmounted } from 'vue'

/**
 * Composable for showing toast notifications.
 *
 * @param {number} defaultDuration - Default duration in ms (default: 2500)
 * @returns {Object} Toast management functions and state
 */
export function useToast(defaultDuration = 2500) {
  const message = ref('')
  const isVisible = ref(false)
  let timeoutId = null

  const clearTimer = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  onUnmounted(() => {
    clearTimer()
  })

  /**
   * Show a toast message
   * @param {string} msg - Message to display
   * @param {number} duration - Duration in ms (optional)
   */
  const show = (msg, duration = defaultDuration) => {
    clearTimer()
    message.value = msg
    isVisible.value = true
    timeoutId = setTimeout(() => {
      message.value = ''
      isVisible.value = false
      timeoutId = null
    }, duration)
  }

  /**
   * Hide toast immediately
   */
  const hide = () => {
    clearTimer()
    message.value = ''
    isVisible.value = false
  }

  return {
    message,
    isVisible,
    show,
    hide
  }
}
