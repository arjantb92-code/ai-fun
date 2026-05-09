<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import AvatarPlaceholder from '@/components/common/AvatarPlaceholder.vue'
import { useAppStore } from '@/stores/appStore'
import type { BalanceList } from '@/types'

interface MemberWithBalance {
  user_id: number
  user: { id: number; name: string; email: string; avatar_url: string | null } | null
  role: 'owner' | 'admin' | 'member'
  joined_at: string | null
  balance: number
}

const props = defineProps<{
  isOpen: boolean
  balanceList: BalanceList | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'member-removed'): void
}>()

const store = useAppStore()
const members = ref<MemberWithBalance[]>([])
const loading = ref(false)
const removing = ref<number | null>(null)
const error = ref('')

const myRole = ref<'owner' | 'admin' | 'member' | null>(null)

const fetchMembers = async () => {
  if (!props.balanceList) return
  loading.value = true
  error.value = ''
  try {
    const res = await store.apiFetch(`/balance-lists/${props.balanceList.id}/members`)
    if (res.ok) {
      members.value = await res.json()
      const me = members.value.find(m => m.user_id === store.currentUser?.id)
      myRole.value = me?.role ?? null
    } else {
      error.value = 'Leden laden mislukt'
    }
  } catch {
    error.value = 'Leden laden mislukt'
  } finally {
    loading.value = false
  }
}

watch(() => props.isOpen, (open) => {
  if (open) fetchMembers()
})

const canRemove = (member: MemberWithBalance): boolean => {
  if (!myRole.value) return false
  const isSelf = member.user_id === store.currentUser?.id
  const isAdmin = myRole.value === 'owner' || myRole.value === 'admin'
  if (!isSelf && !isAdmin) return false
  if (member.role === 'owner' && !isSelf) return false
  return member.balance === 0
}

const removeTooltip = (member: MemberWithBalance): string => {
  if (member.balance !== 0) {
    const dir = member.balance > 0 ? 'te ontvangen' : 'te betalen'
    return `Saldo €${Math.abs(member.balance).toFixed(2)} ${dir} — vereffening vereist`
  }
  if (member.role === 'owner' && member.user_id !== store.currentUser?.id) {
    return 'Eigenaar kan niet verwijderd worden'
  }
  return ''
}

const removeMember = async (member: MemberWithBalance) => {
  if (!props.balanceList || !canRemove(member)) return
  removing.value = member.user_id
  error.value = ''
  try {
    const res = await store.apiFetch(
      `/balance-lists/${props.balanceList.id}/members/${member.user_id}`,
      { method: 'DELETE' }
    )
    if (res.ok) {
      members.value = members.value.filter(m => m.user_id !== member.user_id)
      emit('member-removed')
    } else {
      const data = await res.json()
      error.value = data.error || 'Verwijderen mislukt'
    }
  } catch {
    error.value = 'Verwijderen mislukt'
  } finally {
    removing.value = null
  }
}

const formatBalance = (balance: number): string => {
  if (balance === 0) return '€0,00'
  const sign = balance > 0 ? '+' : '-'
  return `${sign}€${Math.abs(balance).toFixed(2).replace('.', ',')}`
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Leden Beheren" @close="emit('close')">
    <div class="space-y-4">
      <p class="text-zinc-400 text-sm">
        Leden kunnen worden verwijderd als hun saldo <span class="text-white font-bold">€0,00</span> is.
      </p>

      <div v-if="error" class="bg-brand-red/10 border border-brand-red/30 p-3 text-brand-red text-sm font-bold">
        {{ error }}
      </div>

      <div v-if="loading" class="flex items-center justify-center py-8 text-zinc-500 text-sm uppercase font-bold tracking-widest">
        Laden...
      </div>

      <div v-else class="divide-y divide-zinc-800">
        <div
          v-for="member in members"
          :key="member.user_id"
          class="flex items-center gap-3 py-3"
        >
          <!-- Avatar -->
          <div class="shrink-0">
            <img
              v-if="member.user?.avatar_url"
              :src="member.user.avatar_url"
              :alt="member.user?.name"
              class="w-10 h-10 rounded-full object-cover"
            />
            <AvatarPlaceholder v-else :name="member.user?.name" />
          </div>

          <!-- Name + role -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-bold text-white truncate">{{ member.user?.name ?? 'Onbekend' }}</span>
              <span
                v-if="member.user_id === store.currentUser?.id"
                class="text-[10px] uppercase font-black text-zinc-500 tracking-widest"
              >jij</span>
            </div>
            <span class="text-xs text-zinc-500 uppercase tracking-wider font-bold">{{ member.role }}</span>
          </div>

          <!-- Balance badge -->
          <div
            class="text-sm font-black tabular-nums shrink-0"
            :class="{
              'text-green-400': member.balance > 0,
              'text-brand-red': member.balance < 0,
              'text-zinc-500': member.balance === 0,
            }"
          >
            {{ formatBalance(member.balance) }}
          </div>

          <!-- Remove button -->
          <div class="shrink-0" :title="removeTooltip(member)">
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-black uppercase tracking-wider border transition-all"
              :class="canRemove(member)
                ? 'border-brand-red text-brand-red hover:bg-brand-red hover:text-white'
                : 'border-zinc-800 text-zinc-700 cursor-not-allowed'"
              :disabled="!canRemove(member) || removing === member.user_id"
              @click="removeMember(member)"
            >
              <span v-if="removing === member.user_id">...</span>
              <span v-else-if="member.user_id === store.currentUser?.id">Verlaten</span>
              <span v-else>Verwijder</span>
            </button>
          </div>
        </div>
      </div>

      <button
        type="button"
        class="w-full border border-zinc-700 px-6 py-3 font-bold uppercase hover:bg-zinc-800 transition-colors italic"
        @click="emit('close')"
      >
        Sluiten
      </button>
    </div>
  </BaseModal>
</template>
