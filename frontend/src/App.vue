<script setup lang="ts">
import { useMainPage } from '@/composables/useMainPage'
import AppHeader from '@/components/layouts/AppHeader.vue'
import TabNav from '@/components/layouts/TabNav.vue'
import ActivityTab from '@/components/layouts/ActivityTab.vue'
import BalanceTab from '@/components/layouts/BalanceTab.vue'
import LoginView from '@/components/features/auth/LoginView.vue'
import TransactionModal from '@/components/features/transactions/TransactionModal.vue'
import ProfileModal from '@/components/features/auth/ProfileModal.vue'
import BankImportModal from '@/components/features/transactions/BankImportModal.vue'
import ActivityModal from '@/components/features/activities/ActivityModal.vue'
import BulkActivityModal from '@/components/features/bulk/BulkActivityModal.vue'
import BulkSplitsModal from '@/components/features/bulk/BulkSplitsModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'


const {
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
} = useMainPage()
</script>

<template>
  <div class="min-h-screen bg-trainmore-dark text-white font-industrial p-4 md:p-8 flex flex-col">
    <LoginView v-if="!store.isAuthenticated" :error="loginError" @login="handleLogin" />

    <template v-else>
      <div v-if="store.backendStatus === 'Offline'" class="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
        <div class="bg-red-700 text-white p-8 rounded-lg shadow-2xl text-center">
          <h2 class="text-2xl font-bold mb-4">Verbinding Verbroken!</h2>
          <p class="mb-4">De backend server is niet bereikbaar op <span class="font-mono bg-black/30 p-1 rounded">http://localhost:5001</span>.</p>
          <p>Controleer of de server draait en probeer het opnieuw.</p>
        </div>
      </div>
      <AppHeader @open-profile="isProfileModalOpen = true">
        <template #actions>
          <div class="flex gap-4 w-full md:w-auto text-white">
            <button type="button" class="bg-white text-black px-8 py-3 font-bold uppercase hover:bg-brand-red hover:text-white transition-all transform active:scale-95 italic text-sm shadow-xl" @click="isImportModalOpen = true">Bank Import</button>
            <button type="button" class="border-2 border-brand-red text-brand-red px-8 py-3 font-bold uppercase hover:bg-brand-red hover:text-white transition-all transform active:scale-95 italic text-sm" @click="createNewEntry">Nieuwe Post</button>
          </div>
        </template>
      </AppHeader>

      <div class="flex-1 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8">
        <TabNav
          :current-tab="currentTab"
          :selected-activity-id="selectedActivityId"
          :activities="store.activities"
          @update:current-tab="currentTab = $event"
          @select-activity="selectActivity"
          @new-activity="openActivityModal()"
        />
        <div class="lg:col-span-10">
          <ActivityTab
            v-if="currentTab === 'ACTIVITY'"
            :transactions="store.transactions"
            :deleted-transactions="store.deletedTransactions"
            :selected-activity-id="selectedActivityId"
            :selection="selection"
            @open-transaction="openTransaction"
            @create-entry="createNewEntry"
            @open-bulk-activity="isBulkActivityModalOpen = true"
            @open-bulk-splits="isBulkSplitsModalOpen = true"
          />
          <BalanceTab
            v-if="currentTab === 'BALANCE'"
            :settle-loading="settleLoading"
            :selected-activity-id="selectedActivityId"
            @settle="handleSettle"
            @restore="handleSettlementRestore"
            @delete="handleSettlementDelete"
            @delete-permanent="handleSettlementDeletePermanent"
          />
        </div>
      </div>

      <TransactionModal
        :is-open="isEditModalOpen"
        :transaction="selectedTransaction"
        :users="store.users"
        :group-members="store.groupMembers"
        :activities="store.activities"
        @close="isEditModalOpen = false"
        @save="handleSave"
        @delete="handleDelete"
        @upload-receipt="handleReceiptUpload"
      />
      <ProfileModal :is-open="isProfileModalOpen" :user="store.currentUser" @close="isProfileModalOpen = false" @save="handleProfileSave" />
      <BankImportModal :is-open="isImportModalOpen" @close="isImportModalOpen = false" @imported="handleBankImported" />
      <ActivityModal :is-open="isActivityModalOpen" :activity="selectedActivity" @close="isActivityModalOpen = false; selectedActivity = null" @save="handleActivitySave" />
      <BulkActivityModal
        :is-open="isBulkActivityModalOpen"
        :activities="store.activities"
        :initial-activity-id="selectedActivityId"
        @close="isBulkActivityModalOpen = false"
        @apply="handleBulkActivityApply"
      />
      <BulkSplitsModal
        :is-open="isBulkSplitsModalOpen"
        :group-members="store.groupMembers"
        @close="isBulkSplitsModalOpen = false"
        @apply="handleBulkSplitsApply"
      />
      <ConfirmModal />

      <div v-if="toast.isVisible.value" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-brand-red text-white px-6 py-3 font-black uppercase italic text-sm shadow-xl z-50 animate-in fade-in duration-300">
        {{ toast.message.value }}
      </div>
    </template>
  </div>
</template>
