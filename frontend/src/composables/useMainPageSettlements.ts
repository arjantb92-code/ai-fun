import { useAppStore } from '@/stores/appStore'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import type { Ref } from 'vue'

export function useMainPageSettlements(
  store: ReturnType<typeof useAppStore>,
  toast: ReturnType<typeof useToast>,
  selectedActivityId: Ref<number | null>,
  settleLoading: Ref<boolean>
) {
  const { showConfirm } = useConfirm()

  async function handleSettlementRestore(sessionId: number): Promise<void> {
    try {
      const res = await store.apiFetch(`/settlements/${sessionId}/restore`, { method: 'POST' })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        toast.show(data.error || 'Herstellen mislukt')
      }
    } catch {
      toast.show('Herstellen mislukt')
    }
  }

  async function handleSettlementDeletePermanent(sessionId: number): Promise<void> {
    const ok = await showConfirm({ message: 'Definitief verwijderen? Dit kan niet ongedaan.' })
    if (!ok) return
    try {
      const res = await store.apiFetch(`/settlements/${sessionId}/permanent`, { method: 'DELETE' })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        toast.show(data.error || 'Definitief verwijderen mislukt')
      }
    } catch {
      toast.show('Definitief verwijderen mislukt')
    }
  }

  async function handleSettlementDelete(sessionId: number): Promise<void> {
    const ok = await showConfirm({ message: 'Afrekening ongedaan maken? Transacties komen terug in de lijst.' })
    if (!ok) return
    try {
      const res = await store.apiFetch(`/settlements/${sessionId}`, { method: 'DELETE' })
      if (res.ok) {
        toast.show('Afrekening ongedaan gemaakt')
        await store.fetchData(selectedActivityId.value)
      } else {
        const data = await res.json().catch(() => ({})) as { error?: string }
        toast.show(data.error || 'Ongedaan maken mislukt')
      }
    } catch {
      toast.show('Ongedaan maken mislukt')
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
        toast.show(data.message || 'Afrekenen mislukt')
      }
    } catch (e) {
      toast.show('Afrekenen mislukt: ' + ((e as Error).message || 'onbekend'))
    } finally {
      settleLoading.value = false
    }
  }

  return {
    handleSettlementRestore,
    handleSettlementDeletePermanent,
    handleSettlementDelete,
    handleSettle
  }
}
