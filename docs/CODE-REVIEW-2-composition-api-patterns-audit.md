# Composition API Patterns Audit (App-21)

**Branch:** `arjantb92/app-21-code-review-2-composition-api-patterns-audit`

## 1. Composables inventory

| Composable | File | Naming (useXxx) | Notes |
|------------|------|-----------------|--------|
| useMainPage | useMainPage.ts | ✓ | Orchestrator; calls other composables |
| useMainPageTransactions | useMainPageTransactions.ts | ✓ | Receives deps as args |
| useMainPageSettlements | useMainPageSettlements.ts | ✓ | Receives deps as args |
| useMainPageAuth | useMainPageAuth.ts | ✓ | Receives deps as args |
| useConfirm | useConfirm.ts | ✓ | Singleton-style (module-level refs) |
| useToast | useToast.js | ✓ | **Had missing cleanup → fixed** |
| useSplits | useSplits.js | ✓ | Pure state + computed |
| useSelection | useSelection.js | ✓ | Pure state + computed |

All composables use `useXxx` naming. No instantiation in setup (all are invoked as functions).

---

## 2. List of composables (pre-audit) that lacked cleanup

- **useToast.js** – Used `setTimeout` for auto-hide without clearing on unmount. If the component unmounted while a toast was visible, the timeout could fire and update refs on an unmounted instance. **Fixed:** added `onUnmounted` to clear the timer and extracted `clearTimer()` for reuse in `show`/`hide`.

All other composables either have no side effects that need teardown (no `addEventListener`, `setInterval`, or long-lived timers) or only use `onMounted` for one-shot init (e.g. `useMainPage` → `store.fetchData()`). Vue 3 automatically stops `watch` when the component unmounts, so the watcher in `useMainPage` does not require manual cleanup.

---

## 3. Rule of Hooks compliance

- **Composables are not called inside conditionals or loops.**  
  Checked: `App.vue`, `useMainPage.ts`, `ActivityTab.vue`, `BalanceTab.vue`, `AppHeader.vue`, `ConfirmModal.vue`, `BulkSplitsModal.vue`. In all cases, `useXxx()` is called unconditionally at the top level of `setup` (or at the top level of another composable).  
- No violations found.

---

## 4. Reactivity optimizations

| Area | Current | Recommendation |
|------|--------|----------------|
| **useConfirm** | Exposes `isOpen`, `message`, `title`, `confirmOnly` as refs. | Optional: expose `readonly(isOpen)`, `readonly(message)`, etc. to consumers that only need to read, to avoid accidental mutation. Internal mutation via `resolveConfirm` remains. |
| **useSelection** | `ref(new Set())`, value replaced on toggle/selectAll/clear. | Current usage is fine. For very large sets, consider `shallowRef` if you ever hold large object values. |
| **useSplits** | `ref([...])`, array replaced when mutating. | Fine as-is. For very large lists, `shallowRef` could reduce overhead; current arrays are small. |
| **useMainPage** | Many `ref()` for modal state and selected entities. | Optional: `selectedTransaction` and `selectedActivity` could be `shallowRef` if those objects are large and only ever replaced (not mutated in place). |
| **Third-party / non-reactive** | N/A in current composables. | When integrating libs that must not be made reactive (e.g. map instances, canvas), wrap with `markRaw()`. |

No critical over-reactivity found; suggestions are optional optimizations.

---

## 5. Computed vs watchers

| Location | Current | Assessment |
|----------|--------|------------|
| **useSplits** | `totalWeight`, `includedUserIds` as `computed`. | ✓ Correct: derived state from `splits`. |
| **useSelection** | `count`, `hasSelection` as `computed`. | ✓ Correct: derived from `selected`. |
| **useMainPage** | `watch(selectedActivityId, …)` calling `store.fetchData()`. | **Implemented:** debounced (200 ms) + cleanup of debounce timer in `onUnmounted`. |

No misuse of computed for side effects; watcher use is appropriate, with one debounce recommendation.

---

## 6. Debouncing for watchers

- **useMainPage** – **Done:** `selectedActivityId` watcher is debounced (200 ms) and the debounce timer is cleared in `onUnmounted`.

---

## 7. Review checklist summary

| Check | Result |
|-------|--------|
| All composables checked for cleanup | ✓ Done; only useToast needed and was fixed. |
| Rule of Hooks (no composables in conditionals/loops) | ✓ Compliant. |
| Unnecessary reactivity | ✓ No issues; optional `readonly`/`shallowRef`/`markRaw` noted. |
| Computed vs watchers | ✓ Computed used for derived state; watcher used for fetch side effect. |
| Debouncing for watchers | ✓ useMainPage: debounced + cleanup implemented. |

---

## 8. Deliverables summary

### Composables that (pre-fix) had no cleanup

- **useToast.js** – timeout for auto-hide; **fixed** with `onUnmounted` + shared `clearTimer()`.

### Performance recommendations

1. **useMainPage**: Debounced `selectedActivityId` watcher (200 ms) and cleared timer in `onUnmounted` (implemented).
2. **Optional**: In `useConfirm`, expose `readonly()` refs to read-only consumers.
3. **Optional**: Use `shallowRef` for large replace-only data (e.g. big `selectedTransaction`/`selectedActivity` objects or very large `splits`/selection sets) if profiling shows reactivity overhead.

### Refactoring suggestions

1. **useToast**: Already refactored: `onUnmounted` cleanup + `clearTimer()` helper.
2. **useMainPage**: Debounced watch and cleanup implemented (inline 200 ms debounce + `onUnmounted`).
3. **JS → TS**: Consider migrating `useToast.js`, `useSplits.js`, and `useSelection.js` to `.ts` for consistency with the rest of the composables and better type safety.
