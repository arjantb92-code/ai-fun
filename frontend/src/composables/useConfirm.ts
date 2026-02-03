import { ref } from 'vue'

const isOpen = ref(false)
const message = ref('')
const title = ref('Bevestigen')
const confirmOnly = ref(false)
let pendingResolve: ((value: boolean) => void) | null = null

export interface ConfirmOptions {
  message: string
  title?: string
  confirmOnly?: boolean
}

export function useConfirm() {
  const showConfirm = (options: ConfirmOptions | string): Promise<boolean> => {
    const opts = typeof options === 'string' ? { message: options } : options
    return new Promise<boolean>((resolve) => {
      message.value = opts.message
      title.value = opts.title ?? 'Bevestigen'
      confirmOnly.value = opts.confirmOnly ?? false
      pendingResolve = resolve
      isOpen.value = true
    })
  }

  const showAlert = (msg: string, alertTitle = 'Melding'): Promise<void> => {
    return showConfirm({ message: msg, title: alertTitle, confirmOnly: true }).then(() => undefined)
  }

  const resolveConfirm = (value: boolean) => {
    isOpen.value = false
    if (pendingResolve) {
      pendingResolve(value)
      pendingResolve = null
    }
  }

  return { isOpen, message, title, confirmOnly, showConfirm, showAlert, resolveConfirm }
}
