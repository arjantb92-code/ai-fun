import { useAppStore } from '@/stores/appStore'
import { useToast } from '@/composables/useToast'
import { API_BASE } from '@/config/api'
import type { LoginCredentials, ActivityFormData, Activity } from '@/types'
import type { Ref } from 'vue'

export function useMainPageAuth(
  store: ReturnType<typeof useAppStore>,
  toast: ReturnType<typeof useToast>,
  selectedActivityId: Ref<number | null>,
  selectedActivity: Ref<Activity | null>,
  isProfileModalOpen: Ref<boolean>,
  isActivityModalOpen: Ref<boolean>,
  loginError: Ref<string>
) {
  const handleLogin = async (credentials: LoginCredentials): Promise<void> => {
    loginError.value = ''
    try {
      const res = await fetch(`${API_BASE}/login`, {
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

  const handleProfileSave = async ({ name, email }: { name: string; email: string }): Promise<void> => {
    try {
      const res = await store.apiFetch('/users/profile', { method: 'PUT', body: JSON.stringify({ name, email }) })
      if (res.ok) {
        const data = await res.json() as { user: import('@/types').User }
        store.setCurrentUser(data.user)
        isProfileModalOpen.value = false
      }
    } catch {
      toast.show('Profiel opslaan mislukt')
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
      const payload = isNew ? { ...data, balance_list_id: store.currentBalanceListId } : data
      const res = await store.apiFetch(endpoint, { method, body: JSON.stringify(payload) })
      if (res.ok) {
        await store.fetchData(selectedActivityId.value)
        isActivityModalOpen.value = false
        selectedActivity.value = null
      }
    } catch {
      toast.show('Activiteit opslaan mislukt')
    }
  }

  const handleActivityDelete = async (id: number): Promise<void> => {
    try {
      const res = await store.apiFetch(`/activities/${id}`, { method: 'DELETE' })
      if (res.ok) {
        isActivityModalOpen.value = false
        selectedActivity.value = null
        selectedActivityId.value = null
        await store.fetchData(null)
        toast.show('Activiteit gearchiveerd')
      } else {
        toast.show('Verwijderen mislukt')
      }
    } catch {
      toast.show('Verwijderen mislukt')
    }
  }

  return {
    handleLogin,
    handleProfileSave,
    selectActivity,
    openActivityModal,
    handleActivitySave,
    handleActivityDelete
  }
}
