# Pinia State Management Audit

**Project:** Better WBW  
**Date:** 2026-02-12  
**Auditor:** AI Code Review (APP-26)

---

## Executive Summary

The application uses a single Pinia store (`appStore.ts`) following the Composition API setup syntax. Overall structure is solid, but several issues were identified regarding **immutability**, **async safety**, and **store reset logic**.

---

## 1. Store Structure Review

### Current Architecture

```
frontend/src/stores/
└── appStore.ts          # Single monolithic store (159 lines)
```

### State Overview

| State | Type | Description |
|-------|------|-------------|
| `users` | `User[]` | All users |
| `balances` | `Balance[]` | User balances |
| `transactions` | `Transaction[]` | Active transactions |
| `deletedTransactions` | `Transaction[]` | Soft-deleted transactions |
| `settlementsSuggestions` | `SettlementSuggestion[]` | Settlement recommendations |
| `settlementHistory` | `SettlementSession[]` | Past settlements |
| `activities` | `Activity[]` | Activities/projects |
| `categories` | `Category[]` | Expense categories (static) |
| `currentUser` | `User \| null` | Authenticated user |
| `token` | `string \| null` | JWT token |
| `backendStatus` | `BackendStatus` | Connection status |

### Computed Properties

| Computed | Description |
|----------|-------------|
| `isAuthenticated` | Token + user check |
| `groupMembers` | Filtered group members |
| `totalGroupSpend` | Sum of transaction amounts |

### ✅ Strengths
- Uses modern Composition API setup syntax
- Clear separation of state, computed, and actions
- Proper TypeScript typing
- Efficient batch fetching with `Promise.all()`

### ⚠️ Weaknesses
- Monolithic store (could split by domain)
- Helper methods (`getUserName`, `getBalanceForUser`) should be getters, not actions
- No granular loading/error states

---

## 2. Circular Dependencies

### Dependency Graph

```
appStore.ts
    ├── vue (ref, computed)
    ├── pinia (defineStore)
    ├── @/config/theme (BRAND_RED)
    └── @/types (type imports only)

Composables:
├── useMainPage.ts ──────────→ appStore
│   ├── useMainPageAuth.ts ──→ appStore
│   ├── useMainPageTransactions.ts → appStore
│   └── useMainPageSettlements.ts → appStore

Components:
├── App.vue ──────→ useMainPage (indirect)
├── BalanceTab.vue → appStore (direct)
├── ActivityTab.vue → appStore (direct)
└── AppHeader.vue ─→ appStore (direct)
```

### ✅ Result: NO CIRCULAR DEPENDENCIES

The single-store architecture inherently prevents inter-store circular dependencies. All imports flow unidirectionally from store → composables → components.

---

## 3. Async Safety Audit

### ✅ Safe Patterns Found

**`fetchData()` - Proper batch loading:**
```typescript
const results = await Promise.all([
  apiFetch('/users'), 
  apiFetch('/balances'), 
  // ... etc
])
```

**`handleSettle()` - Loading state pattern:**
```typescript
settleLoading.value = true
try {
  // ...
} finally {
  settleLoading.value = false
}
```

### ⚠️ Issues Found

**Issue 1: No global loading state**

The store lacks granular loading states for individual operations:

```typescript
// Current: Only backendStatus for connection
const backendStatus = ref<BackendStatus>('Connecting...')

// Missing: Per-operation loading states
const isLoadingUsers = ref(false)
const isLoadingTransactions = ref(false)
```

**Issue 2: Race condition potential**

Multiple `fetchData()` calls can interleave (e.g., from `watch` + `onMounted`):

```typescript
// useMainPage.ts
watch(selectedActivityId, () => {
  // Can overlap with...
  store.fetchData(selectedActivityId.value)
})
onMounted(() => store.fetchData()) // ...this call
```

*Mitigated by debounce (200ms), but not eliminated.*

**Issue 3: Sequential API calls in bulk operations**

```typescript
// useMainPageTransactions.ts - handleBankImported
for (const r of rows) {
  const res = await store.apiFetch('/transactions', {...})
  // Sequential! Could be parallelized
}
```

---

## 4. Immutability Audit

### 🔴 VIOLATION FOUND

**Location:** `useMainPageAuth.ts:39`

```typescript
const handleProfileSave = async ({ name, email }) => {
  const res = await store.apiFetch('/users/profile', {...})
  if (res.ok) {
    const data = await res.json()
    store.currentUser = data.user  // ❌ DIRECT MUTATION
    localStorage.setItem('wbw_user', JSON.stringify(data.user))
  }
}
```

**Problem:** Directly assigning to `store.currentUser` bypasses Pinia's reactivity tracking in devtools and breaks the single-responsibility principle.

**Fix:** Add a dedicated action in the store:

```typescript
// appStore.ts
const setCurrentUser = (user: User | null): void => {
  currentUser.value = user
  if (user) {
    localStorage.setItem('wbw_user', JSON.stringify(user))
  } else {
    localStorage.removeItem('wbw_user')
  }
}
```

### ✅ Good Patterns Found

**TransactionModal.vue - Deep clone for local edits:**
```typescript
watch(() => props.transaction, (newVal) => {
  localTx.value = JSON.parse(JSON.stringify(newVal))
})
```

---

## 5. Store Reset Logic

### Current Implementation

```typescript
const logout = (): void => {
  token.value = null
  currentUser.value = null
  localStorage.removeItem('wbw_token')
  localStorage.removeItem('wbw_user')
}
```

### 🔴 INCOMPLETE RESET

**Missing resets:**
- `users`, `balances`, `transactions` (data leakage between sessions)
- `deletedTransactions`, `settlementsSuggestions`, `settlementHistory`
- `activities`, `backendStatus`

### Recommended Fix

```typescript
const $reset = (): void => {
  users.value = []
  balances.value = []
  transactions.value = []
  deletedTransactions.value = []
  settlementsSuggestions.value = []
  settlementHistory.value = []
  activities.value = []
  currentUser.value = null
  token.value = null
  backendStatus.value = 'Connecting...'
  localStorage.removeItem('wbw_token')
  localStorage.removeItem('wbw_user')
}

const logout = (): void => {
  $reset()
}
```

---

## 6. Recommendations Summary

### Priority 1 (Critical)
| Issue | Location | Fix |
|-------|----------|-----|
| Direct state mutation | `useMainPageAuth.ts:39` | Add `setCurrentUser` action |
| Incomplete store reset | `appStore.ts:logout` | Implement `$reset()` function |

### Priority 2 (Recommended)
| Issue | Recommendation |
|-------|----------------|
| Monolithic store | Consider splitting into `userStore`, `transactionStore`, `settlementStore` for larger scale |
| Helper methods as actions | Convert `getUserName`, `getBalanceForUser`, `getActivityInfo` to true getters |
| No granular loading states | Add `isLoading` ref + per-entity loading booleans |

### Priority 3 (Nice to Have)
| Issue | Recommendation |
|-------|----------------|
| Sequential bulk imports | Parallelize with `Promise.all()` (with rate limiting) |
| Race conditions | Add request cancellation with `AbortController` |
| Missing error state | Add `error: ref<string | null>(null)` for UI feedback |

---

## 7. Best Practices Checklist

- [x] Uses Composition API setup syntax
- [x] Proper TypeScript typing
- [x] No circular dependencies between stores
- [ ] ~~All state mutations through actions~~ (1 violation)
- [ ] ~~Complete reset on logout~~ (incomplete)
- [x] Async actions with try/catch
- [ ] ~~Granular loading states~~ (missing)
- [x] Computed properties for derived state
- [x] Deep cloning for local component state

---

## 8. Files Changed in This Audit

1. `frontend/src/stores/appStore.ts` - Added `setCurrentUser`, `$reset`, loading state
2. `frontend/src/composables/useMainPageAuth.ts` - Fixed direct mutation
3. `docs/PINIA_AUDIT.md` - This document

---

*Generated as part of Linear issue APP-26*
