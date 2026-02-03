# Component Structure & Organization Audit

**Linear:** [APP-22 – Code Review 3: Component Structure and Organization Audit](https://linear.app/app-atb/issue/APP-22/code-review-3-component-structure-and-organization-audit)

Gebruik in commits/PR/branch de key **`APP-22`** zodat Linear dit ticket automatisch koppelt.

---

## Review Checklist

| Criterion | Status |
|-----------|--------|
| **Feature-based folder structure** (common/, features/, layouts/) | ✅ |
| **Each component &lt;300 lines** | ✅ All .vue and composables &lt;300 |
| **Filename conventions** (Components PascalCase, Composables camelCase, Types PascalCase, Utils camelCase) | ✅ |
| **Subcomponents exported separate** (e.g. TabNav, ActivityTab, BalanceTab) | ✅ |

---

## 1. Current structure diagram

```
frontend/src/
├── App.vue                          # 152 lines ✅
├── main.js
├── vite-env.d.ts
├── assets/
│   └── main.css
├── components/
│   ├── common/                      # Shared/reusable UI
│   │   ├── BaseModal.vue
│   │   ├── AvatarPlaceholder.vue
│   │   ├── ConfirmModal.vue
│   │   └── index.ts
│   ├── layouts/
│   │   ├── AppHeader.vue
│   │   ├── TabNav.vue
│   │   ├── ActivityTab.vue
│   │   ├── BalanceTab.vue
│   │   └── index.ts
│   └── features/
│       ├── activities/
│       │   ├── ActivityList.vue, ActivityModal.vue, ActivitySelector.vue
│       │   └── index.ts
│       ├── auth/
│       │   ├── LoginView.vue, ProfileModal.vue
│       │   └── index.ts
│       ├── balance/
│       │   ├── BalanceCard.vue, SettlementHistory.vue, SettlementPlan.vue
│       │   └── index.ts
│       ├── bulk/
│       │   ├── BulkActivityModal.vue, BulkSplitsModal.vue
│       │   └── index.ts
│       └── transactions/
│           ├── BankImportModal.vue, TransactionCard.vue, TransactionModal.vue
│           └── index.ts
├── composables/
│   ├── useSelection.js
│   ├── useSplits.js
│   ├── useToast.js
│   ├── useConfirm.ts
│   ├── useMainPage.ts               # 93 lines ✅ (orchestrator)
│   ├── useMainPageTransactions.ts  # 178 lines ✅
│   ├── useMainPageSettlements.ts   # 85 lines ✅
│   └── useMainPageAuth.ts           # 81 lines ✅
├── config/
│   └── categories.js
├── router/
│   └── index.js
├── services/
│   └── .gitkeep
├── stores/
│   └── appStore.ts
├── types/
│   └── index.ts
└── utils/
    └── .gitkeep
```

---

## 2. Components to split list

| File | Lines | Status |
|------|-------|--------|
| App.vue | 152 | ✅ |
| ActivityTab.vue | 261 | ✅ |
| useMainPageTransactions.ts | 178 | ✅ |
| TransactionModal.vue | 194 | ✅ |
| BankImportModal.vue | 185 | ✅ |
| appStore.ts | 158 | ✅ |
| useMainPage.ts | 93 | ✅ (split from 348) |
| All other .vue / composables | &lt;120 | ✅ |

**All components and composables &lt;300 lines.**

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

1. **Branch:** naam bevat `APP-22` (bijv. `APP-22/component-structure-audit`) zodat Linear koppelt.
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

---

## 5. Follow-up (done)

- **useMainPage.ts &gt;300 lines:** Split into `useMainPageTransactions.ts`, `useMainPageSettlements.ts`, `useMainPageAuth.ts`; `useMainPage.ts` now ~93 lines (orchestrator only).
- **ConfirmModal + useConfirm:** In-app dialogs in TrainMore style (no native alert/confirm).
- **common/ConfirmModal.vue** added; doc structure diagram updated.

---

## Koppeling met Linear (APP-22)

Linear koppelt werk aan een issue als de **issue-key** ergens voorkomt:

| Waar | Voorbeeld | Effect in Linear |
|------|-----------|------------------|
| **Branch name** | `APP-22/component-structure-audit` | Issue toont “Linked branches” |
| **Commit message** | `APP-22: split useMainPage` of `Fixes APP-22` | Commits verschijnen bij het issue |
| **PR title/description** | `APP-22 Component structure audit` | PR wordt aan issue gelinkt |

**Zo maak je de koppeling:**

1. **Branch hernoemen** (als je nog niet hebt gepusht):  
   `git branch -m CODE-REVIEW-3/component-structure-audit APP-22/component-structure-audit`

2. **Volgende commits:** begin het bericht met `APP-22` of zet het ergens in de message, bijv.  
   `APP-22: move global styles to main.css`

3. **Bij openen van een PR:** in titel of beschrijving `APP-22` vermelden. Met Linear’s GitHub/GitLab-integratie wordt de PR dan aan het issue gelinkt en zie je die bij [APP-22](https://linear.app/app-atb/issue/APP-22/code-review-3-component-structure-and-organization-audit).
