import { ref, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useToast } from '@/composables/useToast'
import { useSelection } from '@/composables/useSelection'
import type {
  Transaction,
  TransactionSplit,
  LoginCredentials,
  ActivityFormData,
  BankImportRow,
  TabType,
  CategoryKey
} from '@/types'
import type { Activity } from '@/types'

export function useMainPage() {
  const store = useAppStore()
  const toast = useToast()
  const selection = useSelection()

  const currentTab = ref<TabType>('ACTIVITY')
  const selectedActivityId = ref<number | null>(null)
  const isEditModalOpen = ref(false)
  const isImportModalOpen = ref(false)
  const isProfileModalOpen = ref(false)
  const isActivityModalOpen = ref(false)
  const selectedTransaction = ref<Transaction | null>(null)
  const selectedActivity = ref<Activity | null>(null)
  const settleLoading = ref(false)
  const isBulkActivityModalOpen = ref(false)
  const isBulkSplitsModalOpen = ref(false)
  const loginError = ref('')

  const handleLogin = async (credentials: LoginCredentials): Promise<void> => {
    loginError.value = ''
    try {
      const res = await fetch('http://localhost:5001/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      })
      const data = await res.json()
      if (res.ok) {
        store.login(data)
      } else {
        loginError.value = data.message
      }
    } catch {
      loginError.value = 'Server Offline'
    }
  }

  const openTransaction = (t: Transaction): void => {
    selectedTransaction.value = t
    isEditModalOpen.value = true
  }

  const createNewEntry = (): void => {
    const dateStr = new Date().toISOString().split('T')[0]
    const timeStr = new Date().toTimeString().slice(0, 5)
    selectedTransaction.value = {
      id: null,
      description: 'Nieuwe uitgave',
      amount: 0,
      date: dateStr ?? '',
      time: timeStr,
      payer_id: store.currentUser?.id || 0,
      type: 'EXPENSE',
      category: 'overig',
      activity_id: selectedActivityId.value,
      splits: store.groupMembers.map(u => ({ user_id: u.id, weight: 1 }))
    }
    isEditModalOpen.value = true
  }

  const handleSave = async (tx: Transaction): Promise<void> => {
    const isNew = !tx.id
    try {
      const res = await store.apiFetch(isNew ? '/transactions' : `/transactions/${tx.id}`, {
        method: isNew ? 'POST' : 'PUT',
        body: JSON.stringify(tx)
      })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
        isEditModalOpen.value = false
      }
    } catch {
      alert('Opslaan mislukt')
    }
  }

  const handleDelete = async (id: number): Promise<void> => {
    if (!confirm('Naar prullenbak verplaatsen?')) return
    try {
      const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
      const data = await res.json().catch(() => ({})) as { error?: string }
      if (res.ok) {
        toast.show('Verplaatst naar prullenbak')
        await store.fetchData(selectedActivityId.value)
        isEditModalOpen.value = false
      } else if (res.status === 403) {
        alert(data.error || 'Afgerekende transactie kan niet verwijderd worden.')
      } else {
        alert(data.error || 'Verwijderen mislukt')
      }
    } catch {
      alert('Verwijderen mislukt')
    }
  }

  async function handleBulkActivityApply(activityId: number | null): Promise<void> {
    const ids = selection.getSelectedArray()
    if (!ids.length) return
    try {
      const res = await store.apiFetch('/transactions/bulk', {
        method: 'PATCH',
        body: JSON.stringify({ transaction_ids: ids, activity_id: activityId })
      })
      if (res.ok) {
        selection.clear()
        isBulkActivityModalOpen.value = false
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        alert(data.error || 'Bulk update mislukt')
      }
    } catch {
      alert('Bulk update mislukt')
    }
  }

  async function handleBulkSplitsApply(splits: TransactionSplit[]): Promise<void> {
    const ids = selection.getSelectedArray()
    if (!ids.length || !splits.length) return
    try {
      const res = await store.apiFetch('/transactions/bulk', {
        method: 'PATCH',
        body: JSON.stringify({ transaction_ids: ids, splits })
      })
      if (res.ok) {
        selection.clear()
        isBulkSplitsModalOpen.value = false
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        alert(data.error || 'Bulk update mislukt')
      }
    } catch {
      alert('Bulk update mislukt')
    }
  }

  async function handleSettlementRestore(sessionId: number): Promise<void> {
    try {
      const res = await store.apiFetch(`/settlements/${sessionId}/restore`, { method: 'POST' })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        alert(data.error || 'Herstellen mislukt')
      }
    } catch {
      alert('Herstellen mislukt')
    }
  }

  async function handleSettlementDeletePermanent(sessionId: number): Promise<void> {
    if (!confirm('Definitief verwijderen? Dit kan niet ongedaan.')) return
    try {
      const res = await store.apiFetch(`/settlements/${sessionId}/permanent`, { method: 'DELETE' })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        alert(data.error || 'Definitief verwijderen mislukt')
      }
    } catch {
      alert('Definitief verwijderen mislukt')
    }
  }

  async function handleSettlementDelete(sessionId: number): Promise<void> {
    if (!confirm('Afrekening ongedaan maken? Transacties komen terug in de lijst.')) return
    try {
      const res = await store.apiFetch(`/settlements/${sessionId}`, { method: 'DELETE' })
      if (res.ok) {
        toast.show('Afrekening ongedaan gemaakt')
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        alert(data.error || 'Ongedaan maken mislukt')
      }
    } catch {
      alert('Ongedaan maken mislukt')
    }
  }

  const handleReceiptUpload = async (file: File): Promise<void> => {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('http://localhost:5001/ocr/process', {
        method: 'POST',
        headers: { Authorization: `Bearer ${store.token}` },
        body: formData
      })
      const result = await res.json() as { data?: { extracted_data?: { total?: number; merchant?: string } } }
      if (res.ok && selectedTransaction.value) {
        selectedTransaction.value.amount = result.data?.extracted_data?.total ?? selectedTransaction.value.amount
        selectedTransaction.value.description = result.data?.extracted_data?.merchant !== 'Unknown Merchant'
          ? (result.data?.extracted_data?.merchant ?? selectedTransaction.value.description)
          : selectedTransaction.value.description
      }
    } catch {
      alert('OCR mislukt')
    }
  }

  const handleProfileSave = async ({ name, email }: { name: string; email: string }): Promise<void> => {
    try {
      const res = await store.apiFetch('/users/profile', { method: 'PUT', body: JSON.stringify({ name, email }) })
      if (res.ok) {
        const data = await res.json() as { user: import('@/types').User }
        store.currentUser = data.user
        localStorage.setItem('wbw_user', JSON.stringify(data.user))
        isProfileModalOpen.value = false
      }
    } catch {
      alert('Profiel opslaan mislukt')
    }
  }

  const handleBankImported = async (rows: BankImportRow[]): Promise<void> => {
    if (!rows?.length || !store.currentUser || !store.groupMembers?.length) return
    try {
      let ok = 0
      for (const r of rows) {
        const payload = {
          description: r.description || 'Bankimport',
          amount: Math.abs(Number(r.amount)),
          date: r.date || new Date().toISOString().split('T')[0],
          payer_id: store.currentUser.id,
          type: 'EXPENSE' as const,
          category: null as CategoryKey | null,
          activity_id: selectedActivityId.value,
          splits: store.groupMembers.map(u => ({ user_id: u.id, weight: 1 }))
        }
        const res = await store.apiFetch('/transactions', { method: 'POST', body: JSON.stringify(payload) })
        if (res.ok) ok++
      }
      await store.fetchData(selectedActivityId.value)
      isImportModalOpen.value = false
      alert(`${ok} transactie(s) geïmporteerd.`)
    } catch (e) {
      alert('Import mislukt: ' + ((e as Error).message || 'onbekend'))
    }
  }

  const selectActivity = (id: number | null): void => {
    selectedActivityId.value = id
    store.fetchData(id)
  }

  const openActivityModal = (activity: Activity | null = null): void => {
    selectedActivity.value = activity
    isActivityModalOpen.value = true
  }

  const handleActivitySave = async (data: ActivityFormData): Promise<void> => {
    try {
      const isNew = !selectedActivity.value
      const endpoint = isNew ? '/activities' : `/activities/${selectedActivity.value?.id}`
      const method = isNew ? 'POST' : 'PUT'
      const res = await store.apiFetch(endpoint, { method, body: JSON.stringify(data) })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
        isActivityModalOpen.value = false
        selectedActivity.value = null
      }
    } catch {
      alert('Activiteit opslaan mislukt')
    }
  }

  const handleSettle = async (): Promise<void> => {
    settleLoading.value = true
    try {
      const body = selectedActivityId.value ? { activity_id: selectedActivityId.value } : {}
      const res = await store.apiFetch('/settlements/commit', { method: 'POST', body: JSON.stringify(body) })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { message?: string }
        alert(data.message || 'Afrekenen mislukt')
      }
    } catch (e) {
      alert('Afrekenen mislukt: ' + ((e as Error).message || 'onbekend'))
    } finally {
      settleLoading.value = false
    }
  }

  watch(selectedActivityId, () => {
    store.fetchData(selectedActivityId.value)
  })

  onMounted(() => store.fetchData())

  return {
    store,
    toast,
    selection,
    currentTab,
    selectedActivityId,
    isEditModalOpen,
    isImportModalOpen,
    isProfileModalOpen,
    isActivityModalOpen,
    selectedTransaction,
    selectedActivity,
    settleLoading,
    isBulkActivityModalOpen,
    isBulkSplitsModalOpen,
    loginError,
    handleLogin,
    openTransaction,
    createNewEntry,
    handleSave,
    handleDelete,
    handleBulkActivityApply,
    handleBulkSplitsApply,
    handleSettlementRestore,
    handleSettlementDeletePermanent,
    handleSettlementDelete,
    handleReceiptUpload,
    handleProfileSave,
    handleBankImported,
    selectActivity,
    openActivityModal,
    handleActivitySave,
    handleSettle
  }
}
