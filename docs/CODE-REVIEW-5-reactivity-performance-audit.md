# Reactivity & Performance Review (App-24)

**Branch:** `arjantb92/app-24-code-review-5-reactivity-performance-audit`

---

## 1. Reactivity patterns

### ref() for primitives

- **Status: ✓** Primitives use `ref()`: `ref('')`, `ref(false)`, `ref(0)`, `ref<number | null>(null)`, etc. in composables and components. No misuse.

### reactive() for objects

- **Status: ✓ N/A by design** The codebase uses `ref()` for object state (e.g. `ref<Transaction | null>(null)`, `ref<User[]>([])`). In Vue 3, `ref` for objects is valid and avoids the reactivity-loss gotchas of `reactive()` when reassigning. Pinia store uses `ref()` for all state; no `reactive()` used. **No change needed.**

### No unnecessary re-renders

- **Status: ⚠ Minor issues**
  - **ActivityList.vue:** `activities.filter(a => a.is_active)` and `activities.filter(a => !a.is_active)` are used directly in the template. Each re-render runs both filters again. **Fix:** Use computed properties (e.g. `activeActivities`, `archivedActivities`).
  - **BankImportModal.vue:** `selectedCount()` is a method called in the template (`{{ selectedCount() }}`). It runs on every re-render. **Fix:** Use a `computed` so the value is cached until `previewRows` (or selection) changes.
  - **ActivityTab.vue:** `getActivityName(t.activity_id)` is called per transaction in the list. It delegates to `store.getActivityInfo(id)` (array find). For large lists this is O(n) per item per render. Consider a single computed map `activityInfoById` and use it in the template to avoid repeated lookups (optional optimization).

---

## 2. Performance optimizations

### Memoize expensive computations

- **Store:** `totalGroupSpend` is a computed over `transactions` — ✓ memoized.
- **ActivityTab:** `filteredTransactions` and `groupedTransactions` are computed — ✓. Filtering uses `store.getUserName(t.payer_id)` inside the computed; that’s a simple array find and is acceptable.
- **ActivityList:** Filtering in template not memoized — **fixed** via computed (see Deliverables).
- **BankImportModal:** `selectedCount` as method — **fixed** via computed.

### Async components with Suspense for lazy loading

- **Status: ✗ Not used** All components in `App.vue` are statically imported. Modals (TransactionModal, ProfileModal, BankImportModal, ActivityModal, BulkActivityModal, BulkSplitsModal, ConfirmModal) and tabs (ActivityTab, BalanceTab) load up front.
- **Recommendation:** Consider `defineAsyncComponent` for modals that are not shown on initial paint (e.g. TransactionModal, BankImportModal, ActivityModal, Bulk*, ConfirmModal). Wrap the app or a parent in `<Suspense>` if you need a loading state for async components. **Low priority** while bundle size is small.

### Virtual scrolling

- **Status: ✗ Not used** Transaction list in ActivityTab renders all items via `v-for="t in group.txs"`. No virtual list.
- **Recommendation:** For **1000+** transactions, introduce virtual scrolling (e.g. `vue-virtual-scroller` or a similar library) so only visible rows are in the DOM. For typical usage (< 500 items), current approach is acceptable; document the threshold (e.g. “Consider virtual scrolling when list > 1000”).

### Code splitting

- **Router:** Single route with `component: App`; no route-based splitting.
- **Recommendation:** If you add real routes (e.g. `/login`, `/activity/:id`), use `component: () => import('./views/...')` for those routes to get route-based code splitting.

### Watchers optimization

- **No deep watchers** — No `watch(..., { deep: true })` in the codebase. Watchers are on refs or on getters like `() => props.transaction` (reference equality). ✓
- **shallowWatch:** Not used. Current watchers are on primitives or single object references; no need for `shallowWatch` unless you add watches on large nested structures.

### Computed properties instead of methods for derived state

- **Issues found:**
  - **ActivityList.vue:** `activities.filter(...)` in template — derived state should be computed. **Fixed.**
  - **BankImportModal.vue:** `selectedCount()` — derived from `previewRows`; should be computed. **Fixed.**

### keep-alive

- **Status: ✗ Not used** No `<KeepAlive>` around tabs or modals.
- **Recommendation:** Optional. If switching between ActivityTab and BalanceTab is expensive (e.g. heavy setup or many DOM nodes), wrap the tab content in `<KeepAlive>` so the inactive tab isn’t destroyed. Document: “KeepAlive used for tab content to avoid re-running setup and re-fetching when switching tabs.” Only add if you measure a benefit.

---

## 3. Review checklist

| Check | Result |
|-------|--------|
| Reactivity patterns | ✓ ref for primitives; ref for objects (no reactive); minor re-render issues fixed with computed. |
| Expensive computations | ✓ Store and ActivityTab use computed; ActivityList and BankImportModal fixed. |
| Lazy loading opportunities | Modals and routes can use async components; optional. |
| Watcher usage | ✓ No deep watchers; watchers on refs/prop getters. |
| Computed vs methods | ✓ Fixed: ActivityList filters and BankImportModal selectedCount as computed. |

---

## 4. Deliverables

### 4.1 Performance baseline

- **Bundle:** Single app entry; no route-based splitting. All modals and tabs in main bundle.
- **Lists:** Transaction list and deleted list render all items (no virtual scrolling). Group members, categories, and settlement history lists are small.
- **Computed cost:** `filteredTransactions` and `groupedTransactions` depend on `transactions` and filters; they re-run when props or search/category change. Acceptable for typical list sizes.
- **Re-renders:** Before fixes, ActivityList re-ran two filters on every render; BankImportModal re-ran `selectedCount()` on every render. After: derived state is computed and cached.

### 4.2 Reactivity issues list

| Location | Issue | Severity | Status |
|----------|--------|----------|--------|
| ActivityList.vue | `activities.filter(...)` twice in template | Low | **Fixed** — computed |
| BankImportModal.vue | `selectedCount()` method in template | Low | **Fixed** — computed |
| ActivityTab.vue | `getActivityName(t.activity_id)` per row (store lookup) | Optional | Documented; optional map computed |

No incorrect use of `reactive()` or refs; no deep watchers causing unnecessary updates.

### 4.3 Optimization recommendations

1. **Done:** ActivityList — use computed `activeActivities` and `archivedActivities`.
2. **Done:** BankImportModal — use computed `selectedCount`.
3. **Optional:** Lazy-load modals with `defineAsyncComponent` and use `<Suspense>` if you want a smaller initial bundle.
4. **Optional:** For 1000+ transactions, add virtual scrolling on the transaction list.
5. **Optional:** When adding more routes, use `() => import(...)` for route components.
6. **Optional:** Consider `<KeepAlive>` for tab content if tab switching feels slow.

### 4.4 Before/after metrics

- **Before:** ActivityList: two array filters on every re-render. BankImportModal: one filter over preview rows on every re-render.
- **After:** Both use computed properties; recomputation only when source data (activities, previewRows) or selection changes. No instrumentation was run; “after” is structural (computed vs method/inline filter).
- **Suggestion:** For before/after numbers, run a simple benchmark (e.g. render 500 transactions, measure time to interactive or re-render time when toggling search) before and after adding virtual scrolling or keep-alive, if you implement those.

---

## 5. Changes made in this branch

1. **ActivityList.vue** — Added computed properties `activeActivities` and `archivedActivities`; template uses these instead of `activities.filter(...)`.
2. **BankImportModal.vue** — Replaced method `selectedCount()` with computed `selectedCount`; template uses `selectedCount` instead of `selectedCount()`.
