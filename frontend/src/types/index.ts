/**
 * Better WBW - Type Definitions
 * Central type definitions for the expense tracking application
 */

// ============================================================================
// User Types
// ============================================================================

export interface User {
  id: number
  name: string
  email: string
  avatar_url: string | null
  is_group_member: boolean
}

export interface CurrentUser extends User {
  token?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: User
}

// ============================================================================
// Transaction Types
// ============================================================================

export type TransactionType = 'EXPENSE' | 'INCOME' | 'TRANSFER'

export type CategoryKey = 'boodschappen' | 'huishoudelijk' | 'winkelen' | 'vervoer' | 'reizen_vrije_tijd' | 'overig'

export interface TransactionSplit {
  user_id: number
  weight: number
}

export interface Transaction {
  id: number | null
  description: string
  amount: number
  date: string
  time?: string
  payer_id: number
  type: TransactionType
  category?: CategoryKey | null
  activity_id: number | null
  splits: TransactionSplit[]
  deleted_at?: string | null
}

export interface DeletedTransaction extends Transaction {
  deleted_at: string
}

// ============================================================================
// Activity Types
// ============================================================================

export interface Activity {
  id: number
  name: string
  description?: string
  icon: string
  color: string
  start_date?: string | null
  end_date?: string | null
  is_active: boolean
  transaction_count?: number
  total_amount?: number
}

export interface ActivityFormData {
  name: string
  description?: string
  start_date: string | null
  end_date: string | null
  color: string
  icon: string
}

export interface ActivityDisplay {
  name: string
  icon: string
  color: string
}

// ============================================================================
// Balance & Settlement Types
// ============================================================================

export interface Balance {
  user_id: number
  balance: number
}

export interface SettlementSuggestion {
  from_user: string
  to_user: string
  amount: number
}

export interface SettlementResult {
  from_user: string
  to_user: string
  amount: number
}

export interface SettlementTransaction {
  id: number
  description: string
  date: string
  time?: string
  payer?: string
  amount: number
}

export interface SettlementSession {
  id: number
  description?: string
  date: string
  total_amount: number
  results: SettlementResult[]
  transactions: SettlementTransaction[]
  deleted_at?: string | null
}

// ============================================================================
// Bank Import Types
// ============================================================================

export interface BankImportRow {
  _id: number
  date: string
  time?: string
  description: string
  raw_description?: string
  amount: number
  selected: boolean
}

export type BankType = 'ing' | 'abn'

// ============================================================================
// UI State Types
// ============================================================================

export type TabType = 'ACTIVITY' | 'BALANCE'

export type BackendStatus = 'Connecting...' | 'Online' | 'Offline'

// ============================================================================
// Component Props Interfaces
// ============================================================================

export interface AvatarPlaceholderProps {
  name?: string
  size?: string
}

export interface LoginViewProps {
  error?: string
}

export interface ProfileModalProps {
  isOpen: boolean
  user: User | null
}

export interface ActivityListProps {
  activities: Activity[]
  selectedId: number | null
}

export interface ActivityModalProps {
  isOpen: boolean
  activity: Activity | null
}

export interface ActivitySelectorProps {
  activities: Activity[]
  selectedId: number | string | null
  showNone?: boolean
}

export interface TransactionCardProps {
  transaction: Transaction
  payerName?: string
  activity?: ActivityDisplay | null
  selectable?: boolean
  selected?: boolean
}

export interface TransactionModalProps {
  isOpen: boolean
  transaction: Transaction | null
  users: User[]
  groupMembers: User[]
  activities: Activity[]
}

export interface BankImportModalProps {
  isOpen: boolean
}

export interface BalanceCardProps {
  balance: number
  label?: string
}

export interface SettlementPlanProps {
  settlements: SettlementSuggestion[]
  activityName?: string | null
  loading?: boolean
}

export interface SettlementHistoryProps {
  history: SettlementSession[]
}

// ============================================================================
// Component Emit Types
// ============================================================================

export interface LoginViewEmits {
  (e: 'login', credentials: LoginCredentials): void
}

export interface ProfileModalEmits {
  (e: 'close'): void
  (e: 'save', data: { name: string; email: string }): void
}

export interface ActivityListEmits {
  (e: 'select', id: number | null): void
  (e: 'new'): void
  (e: 'archive', id: number): void
}

export interface ActivityModalEmits {
  (e: 'close'): void
  (e: 'save', data: ActivityFormData): void
}

export interface ActivitySelectorEmits {
  (e: 'update:selectedId', id: number | null): void
}

export interface TransactionCardEmits {
  (e: 'click'): void
  (e: 'toggle-select', id: number): void
}

export interface TransactionModalEmits {
  (e: 'close'): void
  (e: 'save', transaction: Transaction): void
  (e: 'delete', id: number): void
  (e: 'upload-receipt', file: File): void
}

export interface BankImportModalEmits {
  (e: 'close'): void
  (e: 'imported', rows: BankImportRow[]): void
}

export interface SettlementPlanEmits {
  (e: 'settle'): void
}

export interface SettlementHistoryEmits {
  (e: 'undo', sessionId: number): void
  (e: 'restore', sessionId: number): void
  (e: 'delete', sessionId: number): void
  (e: 'delete-permanent', sessionId: number): void
}

export interface AppHeaderEmits {
  (e: 'open-profile'): void
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiError {
  error?: string
  message?: string
}

export interface BankImportResponse {
  transactions: Array<{
    date: string
    time?: string
    description: string
    raw_description?: string
    amount: number
  }>
  error?: string
}

export interface OcrResponse {
  data: {
    extracted_data: {
      total?: number
      merchant?: string
    }
  }
}
