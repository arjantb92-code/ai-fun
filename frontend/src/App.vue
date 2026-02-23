<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_BASE as apiBase, API_BASE } from '@/config/api'
import { useMainPage } from '@/composables/useMainPage'
import AppHeader from '@/components/layouts/AppHeader.vue'
import TabNav from '@/components/layouts/TabNav.vue'
import ActivityTab from '@/components/layouts/ActivityTab.vue'
import BalanceTab from '@/components/layouts/BalanceTab.vue'
import LoginView from '@/components/features/auth/LoginView.vue'
import JoinLandingView from '@/components/features/auth/JoinLandingView.vue'
import ActivationView from '@/components/features/auth/ActivationView.vue'
import TransactionModal from '@/components/features/transactions/TransactionModal.vue'
import ProfileModal from '@/components/features/auth/ProfileModal.vue'
import BankImportModal from '@/components/features/transactions/BankImportModal.vue'
import ActivityModal from '@/components/features/activities/ActivityModal.vue'
import BulkActivityModal from '@/components/features/bulk/BulkActivityModal.vue'
import BulkSplitsModal from '@/components/features/bulk/BulkSplitsModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import BalanceListsView from '@/components/features/balance-lists/BalanceListsView.vue'
import InviteModal from '@/components/features/balance-lists/InviteModal.vue'

const route = useRoute()
const router = useRouter()

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

const isInviteModalOpen = ref(false)
const pendingInviteCode = ref<string | null>(null)
const requiresActivation = ref(false)
const activationEmail = ref('')

// Check if we're on the join route with invite code
const isJoinRoute = computed(() => route.name === 'join' && route.params.inviteCode)
const inviteCodeFromRoute = computed(() => route.params.inviteCode as string || '')

// Check if we're on the activation route
const isActivationRoute = computed(() => route.name === 'activate' && route.query.token)
const activationToken = computed(() => route.query.token as string || '')

const handleBackToBalanceLists = () => {
  store.selectBalanceList(null)
}

const handleJoinFromUrl = async () => {
  if (!pendingInviteCode.value || !store.isAuthenticated) return
  
  const code = pendingInviteCode.value
  pendingInviteCode.value = null
  
  const result = await store.joinBalanceList(code)
  if (result.success && result.balanceList) {
    store.selectBalanceList(result.balanceList.id)
    store.fetchData()
    toast.show(result.message)
  } else {
    toast.show(result.message || 'Kon niet deelnemen aan balans')
  }
  
  router.replace('/')
}

// Handle login from join page
const handleJoinLogin = async (credentials: { username: string; password: string }) => {
  requiresActivation.value = false
  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    })
    const data = await res.json()
    if (res.ok) {
      store.login(data)
      // After login, join the balance list
      if (inviteCodeFromRoute.value) {
        pendingInviteCode.value = inviteCodeFromRoute.value
        handleJoinFromUrl()
      }
    } else if (res.status === 403 && data.requires_activation) {
      requiresActivation.value = true
      activationEmail.value = data.email || ''
    } else {
      toast.show(data.message || 'Login failed')
    }
  } catch {
    toast.show('Server Offline')
  }
}

// Handle registration from join page
const handleJoinRegister = async (data: { name: string; email: string; password: string; invite_code: string }) => {
  try {
    const res = await fetch(`${API_BASE}/auth/register-from-invite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    const result = await res.json()
    if (res.ok) {
      store.login({ token: result.token, user: result.user })
      if (result.balance_list) {
        store.selectBalanceList(result.balance_list.id)
        store.fetchData()
      }
      toast.show('Account created! Check your email to activate for future logins.')
      router.replace('/')
    } else {
      toast.show(result.error || 'Registration failed')
    }
  } catch {
    toast.show('Server Offline')
  }
}

// Handle Google login
const handleGoogleLogin = async (inviteCode?: string) => {
  try {
    const url = inviteCode 
      ? `${API_BASE}/auth/google?invite_code=${inviteCode}`
      : `${API_BASE}/auth/google`
    const res = await fetch(url)
    const data = await res.json()
    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      toast.show(data.error || 'Google login not available')
    }
  } catch {
    toast.show('Could not initiate Google login')
  }
}

// Handle Google callback (if code is in URL)
const handleGoogleCallback = async () => {
  const code = route.query.code as string
  const state = route.query.state as string
  if (!code) return
  
  try {
    const res = await fetch(`${API_BASE}/auth/google/callback?code=${code}&state=${state || ''}`)
    const data = await res.json()
    if (res.ok && data.token) {
      store.login({ token: data.token, user: data.user })
      toast.show('Logged in with Google!')
      router.replace('/')
    } else if (data.needs_invite) {
      toast.show('Registration requires an invite link')
      router.replace('/')
    } else {
      toast.show(data.error || 'Google login failed')
      router.replace('/')
    }
  } catch {
    toast.show('Google login failed')
    router.replace('/')
  }
}

// Handle activation complete
const handleActivated = () => {
  toast.show('Account activated! You can now log in.')
  router.replace('/')
}

// Handle resend activation
const handleResendActivation = async (email: string) => {
  try {
    const res = await fetch(`${API_BASE}/auth/resend-activation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    })
    const data = await res.json()
    toast.show(data.message || 'Activation email sent')
  } catch {
    toast.show('Could not resend activation email')
  }
}

// Enhanced login handler with activation check
const handleLoginWithActivationCheck = async (credentials: { username: string; password: string }) => {
  requiresActivation.value = false
  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    })
    const data = await res.json()
    if (res.ok) {
      store.login(data)
    } else if (res.status === 403 && data.requires_activation) {
      requiresActivation.value = true
      activationEmail.value = data.email || ''
    } else {
      // Use the original handleLogin for error handling
      handleLogin(credentials)
    }
  } catch {
    handleLogin(credentials)
  }
}

// Check for Google OAuth callback on mount
watch(() => route.query.code, (code) => {
  if (code && !store.isAuthenticated) {
    handleGoogleCallback()
  }
}, { immediate: true })

// Handle invite code from URL (for authenticated users)
watch(() => route.params.inviteCode, (inviteCode) => {
  if (inviteCode && typeof inviteCode === 'string' && store.isAuthenticated) {
    pendingInviteCode.value = inviteCode
    handleJoinFromUrl()
  }
}, { immediate: true })

// When user logs in, check for pending invite
watch(() => store.isAuthenticated, (isAuth) => {
  if (isAuth && pendingInviteCode.value) {
    handleJoinFromUrl()
  }
})
</script>

<template>
  <div class="min-h-screen bg-trainmore-dark text-white font-industrial flex flex-col">
    <!-- Activation Page -->
    <ActivationView 
      v-if="isActivationRoute" 
      :token="activationToken"
      @activated="handleActivated"
      @go-login="router.replace('/')"
    />

    <!-- Join Landing Page (unauthenticated users with invite code) -->
    <JoinLandingView
      v-else-if="isJoinRoute && !store.isAuthenticated"
      :invite-code="inviteCodeFromRoute"
      @login="handleJoinLogin"
      @register="handleJoinRegister"
      @google-login="handleGoogleLogin"
    />

    <!-- Regular Login -->
    <LoginView 
      v-else-if="!store.isAuthenticated" 
      :error="loginError"
      :requires-activation="requiresActivation"
      :activation-email="activationEmail"
      @login="handleLoginWithActivationCheck" 
      @google-login="() => handleGoogleLogin()"
      @resend-activation="handleResendActivation"
    />

    <!-- Balance List Selection Screen -->
    <BalanceListsView v-else-if="!store.hasSelectedBalanceList" />

    <!-- Main App (scoped to selected balance list) -->
    <template v-else>
      <div class="p-4 md:p-8 flex flex-col flex-1">
        <div v-if="store.backendStatus === 'Offline'" class="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div class="bg-red-700 text-white p-8 rounded-lg shadow-2xl text-center">
            <h2 class="text-2xl font-bold mb-4">Verbinding Verbroken!</h2>
            <p class="mb-4">De backend server is niet bereikbaar op <span class="font-mono bg-black/30 p-1 rounded">{{ apiBase }}</span>.</p>
            <p>Controleer of de server draait en probeer het opnieuw.</p>
          </div>
        </div>

        <AppHeader @open-profile="isProfileModalOpen = true" @logout="store.logout()">
          <template #actions>
            <div class="flex gap-4 w-full md:w-auto text-white items-center">
              <button
                type="button"
                class="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2"
                @click="handleBackToBalanceLists"
              >
                <span>&larr;</span>
                <span class="hidden md:inline">{{ store.currentBalanceList?.name || 'Balansen' }}</span>
              </button>
              <button
                type="button"
                class="text-gray-400 hover:text-white transition-colors text-sm"
                @click="isInviteModalOpen = true"
              >
                Uitnodigen
              </button>
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
        <ProfileModal :is-open="isProfileModalOpen" :user="store.currentUser" @close="isProfileModalOpen = false" @save="handleProfileSave" @logout="isProfileModalOpen = false; store.logout()" />
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
        <InviteModal
          :is-open="isInviteModalOpen"
          :balance-list="store.currentBalanceList"
          @close="isInviteModalOpen = false"
        />
        <ConfirmModal />

        <div v-if="toast.isVisible.value" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-brand-red text-white px-6 py-3 font-black uppercase italic text-sm shadow-xl z-50 animate-in fade-in duration-300">
          {{ toast.message.value }}
        </div>
      </div>
    </template>
  </div>
</template>
