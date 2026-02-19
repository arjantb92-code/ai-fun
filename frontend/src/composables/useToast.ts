import { ref, onUnmounted } from 'vue'

export function useToast(defaultDuration = 2500) {
  const message = ref('')
  const isVisible = ref(false)
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const clearTimer = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  onUnmounted(() => {
    clearTimer()
  })

  const show = (msg: string, duration = defaultDuration) => {
    clearTimer()
    message.value = msg
    isVisible.value = true
    timeoutId = setTimeout(() => {
      message.value = ''
      isVisible.value = false
      timeoutId = null
    }, duration)
  }

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
