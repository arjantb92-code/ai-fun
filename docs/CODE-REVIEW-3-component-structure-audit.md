# [CODE-REVIEW-3] Component Structure & Organization Audit

## 1. Current structure diagram (before → after refactor)

**Before:** `shared/`, `layout/`, App.vue 645 lines. **After:** `common/`, `layouts/`, App.vue 150 lines; tab/layout logic in ActivityTab, BalanceTab, TabNav, useMainPage.

```
frontend/src/
├── App.vue                          # 150 lines ✅ (<300)
├── main.js
├── vite-env.d.ts
├── assets/
│   └── main.css
├── components/
│   ├── common/                      # ✅ Shared/reusable UI
│   │   ├── BaseModal.vue
│   │   ├── AvatarPlaceholder.vue
│   │   └── index.ts
│   ├── layouts/                     # ✅ Layout components
│   │   ├── AppHeader.vue
│   │   ├── TabNav.vue
│   │   ├── ActivityTab.vue
│   │   ├── BalanceTab.vue
│   │   └── index.ts
│   └── features/
│       ├── activities/
│       │   ├── ActivityList.vue
│       │   ├── ActivityModal.vue
│       │   └── ActivitySelector.vue
│       ├── auth/
│       │   ├── LoginView.vue
│       │   └── ProfileModal.vue
│       ├── balance/
│       │   ├── BalanceCard.vue
│       │   ├── SettlementHistory.vue
│       │   └── SettlementPlan.vue
│       ├── bulk/
│       │   ├── BulkActivityModal.vue
│       │   └── BulkSplitsModal.vue
│       └── transactions/
│           ├── BankImportModal.vue
│           ├── TransactionCard.vue
│           └── TransactionModal.vue
├── composables/
│   ├── useSelection.js              # ✅ camelCase
│   ├── useSplits.js
│   ├── useToast.js
│   └── useMainPage.ts               # ✅ Main page state + handlers
├── config/
│   └── categories.js
├── router/
│   └── index.js
├── services/                        # ✅ Added (placeholder)
│   └── .gitkeep
├── stores/
│   └── appStore.ts                 # counter.js removed
├── types/
│   └── index.ts                    # ✅ PascalCase types inside
└── utils/                          # ✅ Added (placeholder)
    └── .gitkeep
```

---

## 2. Components to split list

| File | Lines | Action |
|------|-------|--------|
| **App.vue** | **150** | ✅ Split into: `App.vue` (shell + modals), `ActivityTab.vue`, `BalanceTab.vue`, `TabNav.vue`, `useMainPage.ts`. |
| ActivityTab.vue | 257 | OK (<300) |
| TransactionModal.vue | 194 | OK |
| BankImportModal.vue | 185 | OK |
| appStore.ts | 158 | OK |
| All other .vue | &lt;120 | OK |

**Done:** App.vue &lt;300; ActivityTab &lt;300; BalanceTab &lt;80; TabNav &lt;60.

---

## 3. Recommended folder structure

```
frontend/src/
├── components/
│   ├── common/              # Shared/reusable UI (renamed from shared)
│   │   ├── BaseModal.vue
│   │   ├── AvatarPlaceholder.vue
│   │   └── index.ts
│   ├── layouts/             # Layout components (renamed from layout)
│   │   ├── AppHeader.vue
│   │   └── index.ts
│   └── features/
│       ├── activities/
│       │   ├── ActivityList.vue
│       │   ├── ActivityModal.vue
│       │   ├── ActivitySelector.vue
│       │   └── index.ts
│       ├── auth/
│       │   ├── LoginView.vue
│       │   ├── ProfileModal.vue
│       │   └── index.ts
│       ├── balance/
│       │   ├── BalanceCard.vue
│       │   ├── SettlementHistory.vue
│       │   ├── SettlementPlan.vue
│       │   └── index.ts
│       ├── bulk/
│       │   ├── BulkActivityModal.vue
│       │   ├── BulkSplitsModal.vue
│       │   └── index.ts
│       └── transactions/
│           ├── BankImportModal.vue
│           ├── TransactionCard.vue
│           ├── TransactionModal.vue
│           └── index.ts
├── composables/             # camelCase (useUser.ts style)
├── stores/
├── services/                # New: API / domain services
├── types/                   # PascalCase type names
├── utils/                   # New: camelCase (formatting.ts etc.)
└── config/
```

**Filename conventions (verified):**
- Components: PascalCase (UserForm.vue) ✅
- Composables: camelCase (useUser.ts) — current .js OK, .ts preferred later
- Types: PascalCase (User.ts or index.ts with PascalCase exports) ✅
- Utils: camelCase (formatting.ts) ✅

---

## 4. Refactoring plan

1. **Branch:** `CODE-REVIEW-3/component-structure-audit` (Linear link via branch name).
2. **Rename folders:** `shared/` → `common/`, `layout/` → `layouts/`.
3. **Add missing dirs:** `services/`, `utils/` (with `.gitkeep` or placeholder).
4. **Remove dead code:** Delete `stores/counter.js` (unused).
5. **Split App.vue:**
   - Extract **TabNav.vue**: tab buttons (ACTIVITY / BALANCE) + ActivityList sidebar. Props: `currentTab`, `selectedActivityId`, `activities`. Emits: `update:currentTab`, `select-activity`, `new-activity`.
   - Extract **ActivityTab.vue**: trash toggle, search, category filter, selection bar, grouped transaction list, trash list. Uses store + useSelection + useToast; emits `open-transaction`, `create-entry`, `open-bulk-activity`, `open-bulk-splits`.
   - Extract **BalanceTab.vue**: BalanceCard, status-per-person block, SettlementPlan, SettlementHistory. Uses store; props: `settleLoading`, `selectedActivityId`; emits/handlers for settle and history actions.
   - **App.vue** keeps: shell, LoginView, BackendOffline banner, AppHeader, TabNav + ActivityTab/BalanceTab, all modals, toast; delegates tab content to ActivityTab/BalanceTab.
6. **Barrel exports:** Add `index.ts` per feature and for `common/`, `layouts/`; update all imports to use `@/components/common`, `@/components/layouts`, or feature barrels.
7. **Subcomponents:** ActivityTab/BalanceTab/TabNav are the new “subcomponents” exported as separate files; no nested UserFormSection-style needed for current scope.
8. **Optional follow-up:** Migrate composables to `.ts`; add feature-level composables (e.g. `features/auth/composables/useUser.ts`) if logic grows.
