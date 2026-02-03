import { useAppStore } from '@/stores/appStore'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import type { Transaction, TransactionSplit, BankImportRow, CategoryKey } from '@/types'
import type { Ref } from 'vue'

export function useMainPageTransactions(
  store: ReturnType<typeof useAppStore>,
  toast: ReturnType<typeof useToast>,
  selection: ReturnType<typeof import('./useSelection').useSelection>,
  selectedActivityId: Ref<number | null>,
  selectedTransaction: Ref<Transaction | null>,
  isEditModalOpen: Ref<boolean>,
  isImportModalOpen: Ref<boolean>,
  isBulkActivityModalOpen: Ref<boolean>,
  isBulkSplitsModalOpen: Ref<boolean>
) {
  const { showConfirm } = useConfirm()

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
      toast.show('Opslaan mislukt')
    }
  }

  const handleDelete = async (id: number): Promise<void> => {
    const ok = await showConfirm({ message: 'Naar prullenbak verplaatsen?' })
    if (!ok) return
    try {
      const res = await store.apiFetch(`/transactions/${id}`, { method: 'DELETE' })
      const data = await res.json().catch(() => ({})) as { error?: string }
      if (res.ok) {
        toast.show('Verplaatst naar prullenbak')
        await store.fetchData(selectedActivityId.value)
        isEditModalOpen.value = false
      } else if (res.status === 403) {
        toast.show(data.error || 'Afgerekende transactie kan niet verwijderd worden.')
      } else {
        toast.show(data.error || 'Verwijderen mislukt')
      }
    } catch {
      toast.show('Verwijderen mislukt')
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
        toast.show(data.error || 'Bulk update mislukt')
      }
    } catch {
      toast.show('Bulk update mislukt')
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
        toast.show(data.error || 'Bulk update mislukt')
      }
    } catch {
      toast.show('Bulk update mislukt')
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
      toast.show('OCR mislukt')
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
      toast.show(`${ok} transactie(s) geïmporteerd.`)
    } catch (e) {
      toast.show('Import mislukt: ' + ((e as Error).message || 'onbekend'))
    }
  }

  return {
    openTransaction,
    createNewEntry,
    handleSave,
    handleDelete,
    handleBulkActivityApply,
    handleBulkSplitsApply,
    handleReceiptUpload,
    handleBankImported
  }
}
