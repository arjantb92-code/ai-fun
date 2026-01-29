# Refactoring Plan: Better WBW - DRY & OOP Improvements

> **Doel:** Duplicate code elimineren, DRY principes toepassen, code leesbaarheid verbeteren, en Vue best practices implementeren. De frontend moet visueel identiek blijven.

---

## Inhoudsopgave

1. [Executive Summary](#executive-summary)
2. [Frontend Refactoring](#frontend-refactoring)
   - [Category Configuration Consolidatie](#1-category-configuration-consolidatie)
   - [Base Modal Component](#2-base-modal-component)
   - [Reusable Form Components](#3-reusable-form-components)
   - [Composables voor Shared Logic](#4-composables-voor-shared-logic)
   - [App.vue Opsplitsen](#5-appvue-opsplitsen)
   - [Store Verbeteringen](#6-store-verbeteringen)
3. [Backend Refactoring](#backend-refactoring)
   - [Balance Calculator Service](#7-balance-calculator-service)
   - [Transaction Serializer](#8-transaction-serializer)
   - [Settlement Service](#9-settlement-service)
   - [Error Handling Patterns](#10-error-handling-patterns)
4. [Vue Best Practices Referenties](#vue-best-practices)
5. [Implementatie Volgorde](#implementatie-volgorde)

---

## Executive Summary

### Huidige Problemen

| Probleem | Impact | Prioriteit |
|----------|--------|------------|
| Category config in 3 plekken | Inconsistentie risico | Hoog |
| Modal wrapper code 5x gedupliceerd | ~150 regels duplicaat | Hoog |
| App.vue 700+ regels | Moeilijk onderhoudbaar | Hoog |
| Balance berekening 4x gedupliceerd | Bug risico | Hoog |
| Form styling 20+ keer herhaald | Inconsistentie | Medium |
| Split weight logic 2x gedupliceerd | Bug risico | Medium |

### Verwachte Verbetering

- **~40% code reductie** in frontend
- **~30% code reductie** in backend
- **Betere testbaarheid** door separation of concerns
- **Consistentere UI** door shared components

---

## Frontend Refactoring

### 1. Category Configuration Consolidatie

**Probleem:** Category configuratie staat op 3 plekken:

```javascript
// TransactionCard.vue - regel 4-11
const CATEGORY_CONFIG = {
  boodschappen: { label: 'Boodschappen', icon: '🛒', color: '#22c55e' },
  // ...
}

// TransactionModal.vue - regel 5-12
const CATEGORIES = [
  { key: 'boodschappen', label: 'Boodschappen', icon: '🛒' },
  // ...
]

// appStore.js - regel 12-19
const categories = ref([
  { key: 'boodschappen', label: 'Boodschappen' },
  // ...
])
```

**Oplossing:** Maak één centrale configuratie:

```javascript
// src/config/categories.js
export const CATEGORIES = {
  boodschappen: { key: 'boodschappen', label: 'Boodschappen', icon: '🛒', color: '#22c55e' },
  huishoudelijk: { key: 'huishoudelijk', label: 'Huishoudelijk', icon: '🏠', color: '#f59e0b' },
  winkelen: { key: 'winkelen', label: 'Winkelen', icon: '🛍️', color: '#ec4899' },
  vervoer: { key: 'vervoer', label: 'Vervoer', icon: '🚗', color: '#3b82f6' },
  reizen_vrije_tijd: { key: 'reizen_vrije_tijd', label: 'Reizen & Vrije Tijd', icon: '✈️', color: '#8b5cf6' },
  overig: { key: 'overig', label: 'Overig', icon: '📦', color: '#6b7280' }
}

export const getCategoryConfig = (key) => CATEGORIES[key] || CATEGORIES.overig
export const getCategoryList = () => Object.values(CATEGORIES)
```

---

### 2. Base Modal Component

**Probleem:** Alle modals gebruiken identieke wrapper code (~30 regels per modal):

```vue
<!-- Herhaald in: TransactionModal, ProfileModal, ActivityModal, BankImportModal, App.vue (2x) -->
<Transition name="fade">
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="$emit('close')"></div>
    <div class="bg-industrial-gray w-full max-w-md border border-zinc-800 shadow-2xl relative overflow-hidden text-white">
      <div class="h-1 bg-brand-red absolute top-0 left-0 right-0"></div>
      <!-- content -->
    </div>
  </div>
</Transition>
```

**Oplossing:** Maak een `BaseModal.vue`:

```vue
<!-- src/components/shared/BaseModal.vue -->
<script setup>
defineProps({
  isOpen: Boolean,
  maxWidth: { type: String, default: 'max-w-md' },
  title: String
})

defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/95 backdrop-blur-md" @click="$emit('close')"></div>
        <div :class="['bg-industrial-gray w-full border border-zinc-800 shadow-2xl relative overflow-hidden text-white', maxWidth]">
          <div class="h-1 bg-brand-red absolute top-0 left-0 right-0"></div>
          <div class="p-8">
            <div v-if="title" class="flex justify-between items-center mb-6">
              <h2 class="text-2xl font-black uppercase italic tracking-tighter">{{ title }}</h2>
              <button @click="$emit('close')" class="text-zinc-600 hover:text-white text-xl leading-none">×</button>
            </div>
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
```

**Gebruik:**
```vue
<BaseModal :is-open="isOpen" title="Profiel" @close="$emit('close')">
  <!-- Modal content -->
</BaseModal>
```

---

### 3. Reusable Form Components

**Probleem:** Dezelfde input/button styles 20+ keer herhaald:

```html
<!-- Input style herhaald overal -->
<input class="w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase outline-none italic text-sm text-white focus:border-brand-red">

<!-- Label style herhaald -->
<label class="block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2">

<!-- Primary button herhaald -->
<button class="bg-brand-red text-white py-4 font-black uppercase italic">

<!-- Secondary button herhaald -->
<button class="border border-zinc-700 text-zinc-400 hover:text-white">
```

**Oplossing A - Tailwind @apply classes in CSS:**

```css
/* src/assets/main.css */
@layer components {
  .input-industrial {
    @apply w-full bg-zinc-900 border border-zinc-800 p-4 font-black uppercase 
           outline-none italic text-sm text-white focus:border-brand-red transition-all;
  }
  
  .label-industrial {
    @apply block text-xs font-black uppercase tracking-widest text-zinc-500 mb-2;
  }
  
  .btn-primary {
    @apply bg-brand-red text-white py-4 font-black uppercase italic 
           hover:bg-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed;
  }
  
  .btn-secondary {
    @apply border border-zinc-700 text-zinc-400 py-4 font-black uppercase italic
           hover:text-white hover:border-zinc-500 transition-all;
  }
  
  .btn-danger {
    @apply border border-zinc-800 text-zinc-600 font-black uppercase italic
           hover:text-red-500 hover:border-red-500 transition-all;
  }
}
```

**Oplossing B - Form components:**

```vue
<!-- src/components/shared/FormInput.vue -->
<script setup>
const model = defineModel()
defineProps({
  label: String,
  type: { type: String, default: 'text' },
  placeholder: String
})
</script>

<template>
  <div>
    <label v-if="label" class="label-industrial">{{ label }}</label>
    <input v-model="model" :type="type" :placeholder="placeholder" class="input-industrial">
  </div>
</template>
```

---

### 4. Composables voor Shared Logic

**Probleem:** Split weight management logic is gedupliceerd in TransactionModal en App.vue:

```javascript
// In TransactionModal.vue
const toggleUserInSplit = (userId) => {
  const idx = localTx.value.splits.findIndex(s => s.user_id === userId)
  if (idx !== -1) localTx.value.splits.splice(idx, 1)
  else localTx.value.splits.push({ user_id: userId, weight: 1 })
}

const incrementWeight = (uId) => {
  const s = localTx.value.splits.find(s => s.user_id === uId)
  if (s) s.weight++
}

// Vrijwel identiek in App.vue voor bulk splits
```

**Oplossing:** Maak een composable:

```javascript
// src/composables/useSplits.js
import { ref, computed } from 'vue'

export function useSplits(initialSplits = []) {
  const splits = ref([...initialSplits])

  const toggleUser = (userId) => {
    const idx = splits.value.findIndex(s => s.user_id === userId)
    if (idx !== -1) {
      splits.value.splice(idx, 1)
    } else {
      splits.value.push({ user_id: userId, weight: 1 })
    }
  }

  const incrementWeight = (userId) => {
    const split = splits.value.find(s => s.user_id === userId)
    if (split) split.weight++
  }

  const decrementWeight = (userId) => {
    const split = splits.value.find(s => s.user_id === userId)
    if (split && split.weight > 1) split.weight--
  }

  const isUserIncluded = (userId) => splits.value.some(s => s.user_id === userId)
  
  const getWeight = (userId) => splits.value.find(s => s.user_id === userId)?.weight ?? 0

  const reset = (newSplits = []) => {
    splits.value = [...newSplits]
  }

  return {
    splits,
    toggleUser,
    incrementWeight,
    decrementWeight,
    isUserIncluded,
    getWeight,
    reset
  }
}
```

**Andere composables om te maken:**

```javascript
// src/composables/useToast.js
export function useToast() {
  const message = ref('')
  
  const show = (msg, duration = 2500) => {
    message.value = msg
    setTimeout(() => { message.value = '' }, duration)
  }
  
  return { message, show }
}

// src/composables/useSelection.js
export function useSelection() {
  const selected = ref(new Set())
  
  const toggle = (id) => {
    const s = new Set(selected.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    selected.value = s
  }
  
  const selectAll = (ids) => { selected.value = new Set(ids) }
  const clear = () => { selected.value = new Set() }
  const isSelected = (id) => selected.value.has(id)
  const count = computed(() => selected.value.size)
  
  return { selected, toggle, selectAll, clear, isSelected, count }
}

// src/composables/useApi.js
export function useApi(store) {
  const loading = ref(false)
  const error = ref(null)

  const execute = async (fn) => {
    loading.value = true
    error.value = null
    try {
      return await fn()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, error, execute }
}
```

---

### 5. App.vue Opsplitsen

**Probleem:** App.vue is 700+ regels met:
- 20+ refs voor UI state
- 25+ methods voor API calls
- 2 inline modals
- Complexe template

**Oplossing:** Splits in feature containers:

```
src/
├── views/
│   └── MainView.vue          # Huidige App.vue content (authenticated)
├── components/
│   ├── features/
│   │   ├── transactions/
│   │   │   ├── TransactionList.vue      # Grouped transactions display
│   │   │   ├── TransactionFilters.vue   # Search + category filter
│   │   │   ├── TransactionBulkBar.vue   # Selection actions bar
│   │   │   └── TrashView.vue            # Deleted transactions
│   │   ├── bulk/
│   │   │   ├── BulkActivityModal.vue    # Uit App.vue halen
│   │   │   └── BulkSplitsModal.vue      # Uit App.vue halen
```

**Nieuwe App.vue (minimaal):**

```vue
<script setup>
import { useAppStore } from '@/stores/appStore'
import LoginView from '@/components/features/auth/LoginView.vue'
import MainView from '@/views/MainView.vue'

const store = useAppStore()
</script>

<template>
  <div class="min-h-screen bg-trainmore-dark text-white font-industrial">
    <LoginView v-if="!store.isAuthenticated" />
    <MainView v-else />
  </div>
</template>
```

---

### 6. Store Verbeteringen

**Probleem:** Computed values en helpers ontbreken in store:

```javascript
// Huidig - in App.vue
const filteredTransactions = computed(() => {
  let result = store.transactions
  if (selectedCategoryFilter.value) {
    result = result.filter(t => t.category === selectedCategoryFilter.value)
  }
  // ...
})

const getPayerName = (id) => store.users.find(u => u.id === id)?.name || 'Onbekend'
```

**Oplossing:** Verplaats naar store:

```javascript
// src/stores/appStore.js
export const useAppStore = defineStore('app', () => {
  // ... existing state ...

  // Computed getters
  const activeActivities = computed(() => 
    activities.value.filter(a => a.is_active)
  )
  
  const archivedActivities = computed(() => 
    activities.value.filter(a => !a.is_active)
  )

  // Helper methods
  const getUserById = (id) => users.value.find(u => u.id === id)
  const getUserName = (id) => getUserById(id)?.name || 'Onbekend'
  const getActivityById = (id) => activities.value.find(a => a.id === id)
  const getBalanceForUser = (userId) => 
    balances.value.find(b => b.user_id === userId)?.balance || 0

  // Transaction filtering (met parameters)
  const getFilteredTransactions = (categoryFilter, searchQuery) => {
    let result = transactions.value
    if (categoryFilter) {
      result = result.filter(t => t.category === categoryFilter)
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(t => 
        t.description.toLowerCase().includes(q) || 
        getUserName(t.payer_id).toLowerCase().includes(q)
      )
    }
    return result
  }

  return {
    // ... existing ...
    activeActivities,
    archivedActivities,
    getUserById,
    getUserName,
    getActivityById,
    getBalanceForUser,
    getFilteredTransactions
  }
})
```

---

## Backend Refactoring

### 7. Balance Calculator Service

**Probleem:** Balance berekening 4x gedupliceerd (~30 regels per keer):

```python
# Herhaald in: get_balances, suggest_settlement, commit_settlement, get_activity_balance
bals = {u.id: 0.0 for u in users}
for t in txs:
    amt = t.amount; tp = t.type or "EXPENSE"
    if t.payer_id in bals:
        if tp in ["EXPENSE", "TRANSFER"]: bals[t.payer_id] += amt
        else: bals[t.payer_id] -= amt
    tw = sum(s.weight for s in t.splits)
    if tw > 0:
        ppw = amt / tw
        for s in t.splits:
            if s.user_id in bals:
                if tp in ["EXPENSE", "TRANSFER"]: bals[s.user_id] -= ppw * s.weight
                else: bals[s.user_id] += ppw * s.weight
```

**Oplossing:** Maak een service:

```python
# backend/services/balance_service.py
from models import User, Transaction

class BalanceService:
    @staticmethod
    def calculate_balances(transactions, users=None):
        """
        Bereken balans per gebruiker op basis van transacties.
        Positief = tegoed, Negatief = schuld
        """
        if users is None:
            users = User.query.all()
        
        balances = {u.id: 0.0 for u in users}
        
        for tx in transactions:
            amount = tx.amount
            tx_type = tx.type or "EXPENSE"
            
            # Payer krijgt credit
            if tx.payer_id in balances:
                if tx_type in ["EXPENSE", "TRANSFER"]:
                    balances[tx.payer_id] += amount
                else:
                    balances[tx.payer_id] -= amount
            
            # Splits verdelen de kosten
            total_weight = sum(s.weight for s in tx.splits)
            if total_weight > 0:
                per_weight = amount / total_weight
                for split in tx.splits:
                    if split.user_id in balances:
                        if tx_type in ["EXPENSE", "TRANSFER"]:
                            balances[split.user_id] -= per_weight * split.weight
                        else:
                            balances[split.user_id] += per_weight * split.weight
        
        return {uid: round(bal, 2) for uid, bal in balances.items()}

    @staticmethod
    def get_unsettled_transactions(activity_id=None):
        """Haal alle niet-afgerekende, niet-verwijderde transacties op."""
        query = Transaction.query.filter_by(settlement_session_id=None)
        query = query.filter(Transaction.deleted_at.is_(None))
        if activity_id is not None:
            query = query.filter_by(trip_id=activity_id)
        return query.all()
```

---

### 8. Transaction Serializer

**Probleem:** Transaction JSON conversie herhaald:

```python
# Herhaald in meerdere endpoints
{
    "id": t.id,
    "date": t.date.isoformat(),
    "time": t.time or "00:00",
    "description": t.description,
    "amount": t.amount,
    # ... meer velden
}
```

**Oplossing:** Voeg serialize method toe aan model:

```python
# backend/models.py
class Transaction(db.Model):
    # ... existing fields ...
    
    def to_dict(self, include_splits=True):
        data = {
            "id": self.id,
            "date": self.date.isoformat(),
            "time": self.time or "00:00",
            "description": self.description,
            "amount": self.amount,
            "type": self.type or "EXPENSE",
            "category": self.category or "overig",
            "payer_id": self.payer_id,
            "activity_id": self.trip_id,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if include_splits:
            data["splits"] = [
                {"user_id": s.user_id, "weight": s.weight} 
                for s in self.splits
            ]
        return data

class User(db.Model):
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "is_group_member": self.is_group_member
        }
```

---

### 9. Settlement Service

**Probleem:** Settlement suggestie algoritme gedupliceerd:

```python
# Herhaald in suggest_settlement en commit_settlement
dbtr = [[uid, abs(bal)] for uid, bal in bals.items() if bal < -0.01]
crtr = [[uid, bal] for uid, bal in bals.items() if bal > 0.01]
dbtr.sort(key=lambda x: x[1], reverse=True)
crtr.sort(key=lambda x: x[1], reverse=True)
# ... matching algorithm ...
```

**Oplossing:**

```python
# backend/services/settlement_service.py
from models import User

class SettlementService:
    @staticmethod
    def calculate_suggestions(balances, user_map=None):
        """
        Bereken minimale betalingen om schulden te vereffenen.
        Gebruikt greedy algorithm voor debt simplification.
        """
        if user_map is None:
            users = User.query.all()
            user_map = {u.id: u.name for u in users}
        
        # Splits in schuldenaars en crediteuren
        debtors = [[uid, abs(bal)] for uid, bal in balances.items() if bal < -0.01]
        creditors = [[uid, bal] for uid, bal in balances.items() if bal > 0.01]
        
        # Sorteer op bedrag (hoogste eerst)
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)
        
        suggestions = []
        d_idx, c_idx = 0, 0
        
        while d_idx < len(debtors) and c_idx < len(creditors):
            amount = min(debtors[d_idx][1], creditors[c_idx][1])
            suggestions.append({
                "from_user_id": debtors[d_idx][0],
                "from_user": user_map.get(debtors[d_idx][0], "Unknown"),
                "to_user_id": creditors[c_idx][0],
                "to_user": user_map.get(creditors[c_idx][0], "Unknown"),
                "amount": round(amount, 2)
            })
            
            debtors[d_idx][1] -= amount
            creditors[c_idx][1] -= amount
            
            if debtors[d_idx][1] < 0.01:
                d_idx += 1
            if creditors[c_idx][1] < 0.01:
                c_idx += 1
        
        return suggestions
```

---

### 10. Error Handling Patterns

**Probleem:** Dezelfde try/except pattern overal:

```python
try:
    # ... logic ...
    db.session.commit()
    return jsonify({"status": "success"})
except Exception as e:
    db.session.rollback()
    return jsonify({"error": str(e)}), 500
```

**Oplossing:** Decorator:

```python
# backend/utils/decorators.py
from functools import wraps
from flask import jsonify
from models import db

def handle_db_errors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    return decorated

# Gebruik:
@app.route('/transactions', methods=['POST'])
@token_required
@handle_db_errors
def add_transaction(current_user):
    # ... logic zonder try/except ...
```

---

## Vue Best Practices

### Referenties

1. **Official Vue Style Guide**
   - https://vuejs.org/style-guide/

2. **Composition API Best Practices**
   - https://vuejs.org/guide/reusability/composables.html

3. **Component Design Patterns**
   - https://www.patterns.dev/vue

4. **Pinia Best Practices**
   - https://pinia.vuejs.org/cookbook/

### Key Principles

| Principe | Toepassing |
|----------|------------|
| Single Responsibility | Elke component doet één ding |
| DRY | Geen code duplicatie |
| Composition over Inheritance | Composables > mixins |
| Props Down, Events Up | Unidirectional data flow |
| Colocation | Gerelateerde code bij elkaar |

---

## Implementatie Volgorde

### Fase 1: Foundation (Hoog prioriteit)
1. ✅ Maak `src/config/categories.js`
2. ✅ Maak `BaseModal.vue` component
3. ✅ Voeg Tailwind `@apply` classes toe
4. ✅ Maak `BalanceService` in backend

### Fase 2: Composables
5. ✅ Maak `useSplits` composable
6. ✅ Maak `useSelection` composable
7. ✅ Maak `useToast` composable

### Fase 3: Store Improvements
8. ✅ Voeg computed getters toe aan store
9. ✅ Voeg helper methods toe aan store

### Fase 4: Component Extraction
10. ✅ Extract `BulkActivityModal.vue`
11. ✅ Extract `BulkSplitsModal.vue`
12. ✅ Maak `TransactionFilters.vue`

### Fase 5: Backend Services
13. ✅ Maak `SettlementService`
14. ✅ Voeg `to_dict()` toe aan models
15. ✅ Maak error handling decorator

### Fase 6: Final Cleanup
16. ✅ Refactor App.vue met nieuwe components
17. ✅ Update alle modals naar BaseModal
18. ✅ Test alle functionaliteit

---

## Checklist per Refactoring

Voor elke wijziging:
- [ ] Visueel identiek aan origineel
- [ ] Alle functionaliteit werkt
- [ ] Geen console errors
- [ ] Code is gedocumenteerd
- [ ] Git commit met duidelijke message

---

*Document aangemaakt voor ticket APP-34*
