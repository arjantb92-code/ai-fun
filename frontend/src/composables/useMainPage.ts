import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useToast } from '@/composables/useToast'
import { useSelection } from '@/composables/useSelection'
import { useMainPageTransactions } from '@/composables/useMainPageTransactions'
import { useMainPageSettlements } from '@/composables/useMainPageSettlements'
import { useMainPageAuth } from '@/composables/useMainPageAuth'
import type { Transaction, TabType } from '@/types'
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

  const transactions = useMainPageTransactions(
    store,
    toast,
    selection,
    selectedActivityId,
    selectedTransaction,
    isEditModalOpen,
    isImportModalOpen,
    isBulkActivityModalOpen,
    isBulkSplitsModalOpen
  )

  const settlements = useMainPageSettlements(store, toast, selectedActivityId, settleLoading)

  const auth = useMainPageAuth(
    store,
    toast,
    selectedActivityId,
    selectedActivity,
    isProfileModalOpen,
    isActivityModalOpen,
    loginError
  )

  let fetchDebounceId: ReturnType<typeof setTimeout> | null = null
  const FETCH_DEBOUNCE_MS = 200

  watch(selectedActivityId, () => {
    if (fetchDebounceId) clearTimeout(fetchDebounceId)
    fetchDebounceId = setTimeout(() => {
      store.fetchData(selectedActivityId.value)
      fetchDebounceId = null
    }, FETCH_DEBOUNCE_MS)
  })

  onMounted(() => store.fetchData())

  onUnmounted(() => {
    if (fetchDebounceId) clearTimeout(fetchDebounceId)
  })

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
    handleLogin: auth.handleLogin,
    openTransaction: transactions.openTransaction,
    createNewEntry: transactions.createNewEntry,
    handleSave: transactions.handleSave,
    handleDelete: transactions.handleDelete,
    handleBulkActivityApply: transactions.handleBulkActivityApply,
    handleBulkSplitsApply: transactions.handleBulkSplitsApply,
    handleSettlementRestore: settlements.handleSettlementRestore,
    handleSettlementDeletePermanent: settlements.handleSettlementDeletePermanent,
    handleSettlementDelete: settlements.handleSettlementDelete,
    handleReceiptUpload: transactions.handleReceiptUpload,
    handleProfileSave: auth.handleProfileSave,
    handleBankImported: transactions.handleBankImported,
    selectActivity: auth.selectActivity,
    openActivityModal: auth.openActivityModal,
    handleActivitySave: auth.handleActivitySave,
    handleSettle: settlements.handleSettle
  }
}
