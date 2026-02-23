# Error Handling & Validation Review (App-25)

**Linear:** [APP-25 – Code Review 6: Error Handling and Validation Audit](https://linear.app/app-atb/issue/APP-25/code-review-6-error-handling-and-validation-audit)  
**Branch:** `arjantb92/app-25-code-review-6-error-handling-validation-audit`

---

## 1. API calls – try/catch and loading

### Current state

| Location | try/catch | loading state | finally | Error shown to user |
|----------|-----------|---------------|--------|----------------------|
| **appStore.fetchData** | ✓ | — (backendStatus) | ✗ | backendStatus = 'Offline' |
| **appStore.fetchTrash** | ✓ | — | ✗ | deletedTransactions = [] |
| **appStore.apiFetch** | ✗ (throws on 401) | — | — | Caller handles |
| **useMainPageAuth.handleLogin** | ✓ | ✗ | ✗ | loginError ref |
| **useMainPageAuth.handleProfileSave** | ✓ | ✗ | ✗ | toast |
| **useMainPageAuth.handleActivitySave** | ✓ | ✗ | ✗ | toast |
| **useMainPageTransactions** (save/delete/bulk/ocr/bank) | ✓ | ✗ (except implicit) | ✗ | toast |
| **useMainPageSettlements** | ✓ | settleLoading in parent | ✗ | toast |
| **ActivityTab** (delete/restore/permanent) | ✓ | ✗ | ✗ | toast |
| **BankImportModal.doUpload** | ✓ | ✓ loading | ✓ finally | error ref + inline |

### Gaps

1. **Login:** `res.json()` can throw if the server returns non-JSON (e.g. 500 HTML). Use `res.json().catch(() => ({}))` and then read `data.message`; fallback message if missing.
2. **No loading flags** on most API calls (login, profile save, activity save, transaction save/delete, etc.). Buttons stay clickable during request. Optional: add local `loading` refs and `finally { loading = false }` where UX warrants it.
3. **apiFetch** is not wrapped in try/catch; callers are responsible. That’s acceptable; document that all callers must try/catch or handle rejections.

---

## 2. Form validation

### Current state

- **Login:** No client-side validation (empty email/password). Server returns `data.message`; shown in `loginError`. ✓ Server-side only.
- **ProfileModal:** No client-side validation (name/email required, email format). No server error message shown on failure (only toast “Profiel opslaan mislukt”). **Gap:** Show server message if backend returns one (e.g. “Email already in use”).
- **ActivityModal:** Minimal client-side: `required` on name, `:disabled="!name"` on submit. No inline error messages. Server errors only via toast from parent.
- **TransactionModal:** No explicit validation; backend validates. Toast on error.
- **BankImportModal:** Client-side: file type (CSV/TXT). Server error in `error.value` and displayed. ✓ Good.

### Recommendations

1. **Client-side:** Add simple validation where it matters: login (non-empty), profile (non-empty name, optional email format), activity (name required – already there). Show inline errors (e.g. under fields) instead of only toasts where forms are critical.
2. **Server-side:** Keep returning structured errors (e.g. `{ message: "..." }` or `{ error: "..." }`). Frontend already reads these in many places; ensure ProfileModal and ActivityModal also surface server message when present.
3. **Clear messages:** Use consistent wording (e.g. “Vul een e-mailadres in”, “Opslaan mislukt: [server message]”).

---

## 3. Type guards for runtime safety

### Current state

- **types/index.ts** defines `ApiError` (`error?: string; message?: string`) but it is not used as a type guard.
- API responses are cast with `as { error?: string }` or `as { message?: string }` without runtime checks. If the backend returns a different shape, we might show `undefined` or throw.

### Recommendation

Add a small type guard and use it when reading error payloads:

```ts
// e.g. in utils/api.ts or types
export function isApiErrorBody(obj: unknown): obj is ApiError {
  return typeof obj === 'object' && obj !== null && ('message' in obj || 'error' in obj)
}
```

Then use it when parsing: `const data = await res.json().catch(() => ({})); if (isApiErrorBody(data)) { message = data.message ?? data.error ?? 'Fout' }`.

---

## 4. Error boundary component

### Current state

- **No Vue error boundary.** There is no `onErrorCaptured` (or equivalent) and no wrapper component that catches render/component errors and shows a fallback UI.
- If a component throws during render or in a lifecycle hook, the whole app can white-screen.

### Implementation plan

1. **Create `ErrorBoundary.vue`:**
   - Use a child component and catch errors via a small renderless/wrapper approach, or use Vue 3’s **errorCaptured** on a parent. (Vue 3 does not have a React-style Error Boundary component out of the box; you implement it by wrapping the app – or a part of it – in a component that uses `onErrorCaptured` and toggles a fallback slot when an error is caught.)
2. **Suggested structure:**
   - Root component (e.g. `App.vue` or a new `AppWithBoundary.vue`) wraps main content in a component that has `onErrorCaptured`. When an error is captured, set `hasError = true` and render a “Something went wrong” view (and optionally a “Retry” that clears state and remounts).
3. **Scope:** At least wrap the main authenticated shell (tabs + modals). Optionally wrap the whole app.
4. **Logging:** In the error handler, call the logger (see §6) with level `error` and the error details before showing the fallback UI.
5. **Document:** In the component or in this doc, state that the error boundary is for unexpected render/lifecycle errors; API errors continue to be handled in try/catch and shown via toast/refs.

---

## 5. Logging strategy

### Current state

- **No structured logging.** No `console.log` / `console.error` / `console.warn` in the frontend codebase. No log levels or central logger.

### Logging strategy document (deliverable)

**Objectives:** Support debugging and optional future integration with a reporting service (e.g. Sentry), without cluttering the UI.

**Levels:**

- **error:** API failures, unhandled rejections, error boundary captures. Always log in development; in production, send to monitoring if available.
- **warn:** Recoverable issues (e.g. invalid API response shape, fallback used).
- **info:** Optional; high-level actions (e.g. “User logged in”, “Settlement committed”) if you need an audit trail.
- **debug:** Only in development; verbose (e.g. request/response, state changes). Strip or no-op in production.

**Implementation:**

- Add a small **logger** module (e.g. `utils/logger.ts` or `config/logger.ts`) with `error`, `warn`, `info`, `debug`. In dev they can call `console.*`; in production, `debug` is no-op, others can `console.error`/`console.warn` or forward to a service.
- Use the logger in:
  - API catch blocks: `logger.error('Failed to fetch user', { id, error })`
  - Error boundary handler: `logger.error('Component error', { error, componentStack })`
  - Optional: inside `apiFetch` on 401 or non-2xx, `logger.warn('API error', { endpoint, status })`

**No PII in logs:** Avoid logging passwords, tokens, or full user objects. Prefer IDs and endpoint names.

---

## 6. Review checklist

| Check | Result |
|-------|--------|
| All API calls have error handling | ✓ All call sites use try/catch or handle rejection; login JSON parse can throw – fix with .catch(() => ({})). |
| Form validation | ⚠ Partial: BankImport + Activity name; Profile/Login need clearer validation and server message display. |
| Type guards | ✗ Not present; add isApiErrorBody (or similar) and use when parsing error payloads. |
| Error boundaries | ✗ Not present; implement per §4. |
| Logging | ✗ Not present; add logger and strategy per §5. |

---

## 7. Deliverables summary

### 7.1 Error handling issues list

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| Login `res.json()` can throw | Medium | useMainPageAuth.handleLogin | Parse with .catch(() => ({})); read message safely. |
| No loading state on most API calls | Low | Multiple | Optional: add loading refs + finally for key actions. |
| Profile save: server error not shown | Low | useMainPageAuth.handleProfileSave | Parse response body; show data.message or data.error in toast or ref. |
| OCR/Receipt: no res.ok check | Low | useMainPageTransactions.handleReceiptUpload | If !res.ok, show toast with server message or “OCR mislukt”. |
| Store fetchData: JSON parse can throw | Low | appStore.fetchData | Wrap each .json() in try/catch or use .catch(() => ({})) to avoid one bad response taking down the whole fetch. |

### 7.2 Validation recommendations

- **Login:** Require non-empty email/password; show inline error (e.g. “Vul e-mail en wachtwoord in”).
- **Profile:** Require non-empty name; optional email format; show server error (e.g. “E-mail al in gebruik”) when present.
- **Activity:** Keep name required and disabled submit when empty; optionally add “Naam is verplicht” under the field.
- **Transaction:** Rely on backend; optionally add client checks for amount > 0, required description, and show server message in toast.

### 7.3 Error boundary implementation plan

- See **§4** above: add a wrapper component that uses `onErrorCaptured`, sets an error state, and renders a “Something went wrong” (+ optional Retry) view. Wrap the main app or the authenticated shell. Log captured errors with the logger. Document scope and intent.

### 7.4 Logging strategy document

- See **§5** above: introduce levels (error, warn, info, debug), a small logger module, and use it in API error paths and the error boundary. No PII; optional production reporting later.

---

## 8. Changes made in this branch

1. **useMainPageAuth.handleLogin** — Safe JSON parse: `res.json().catch(() => ({}))`; only call `store.login(data)` when `data.token` and `data.user` exist; set `loginError` from `data.message` with fallback “Login mislukt”.
2. **useMainPageAuth.handleProfileSave** — Parse response with `.catch(() => ({}))`; on non-ok show server message via `getApiErrorMessage(data, 'Profiel opslaan mislukt')`; on catch log with `logger.error` and show toast.
3. **utils/logger.ts** — Logger with `error`, `warn`, `info`, `debug` (info/debug no-op in production).
4. **utils/apiGuards.ts** — `isApiErrorBody(obj)` and `getApiErrorMessage(obj, fallback)` for safe API error handling.
5. **docs/CODE-REVIEW-6-error-handling-validation-audit.md** — This document.
