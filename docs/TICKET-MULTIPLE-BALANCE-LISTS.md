# Multiple Balance Lists Feature Specification

**Original ticket:** Meerdere balansen per account + eerste scherm + uitnodigen  
**Linear (optional):** Title `Feature: Meerdere balansen per account, eerste scherm + uitnodigen link/QR` · Labels: feature, backend, frontend, wbw. Script: `python scripts/create_linear_ticket_balance_lists.py` (requires `LINEAR_API_KEY`).

---

## Overview

This document specifies the implementation of multiple balance lists per account for the Better WBW application. Each user can belong to multiple balance lists, and each balance list has its own transactions, balances, and settlements.

## Goals

1. Account linked to **multiple balance lists** (lists with name, currency, participants)
2. **First screen** after login = overview "My Balance Lists"; click on a list → balance/transactions
3. **Invite** via link and/or QR code per balance list

## Data Model

### New Entity: BalanceList

```python
class BalanceList(db.Model):
    __tablename__ = "balance_lists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(3), default='EUR')  # ISO 4217 code
    invite_code = db.Column(db.String(32), unique=True, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    members = db.relationship("BalanceListMember", back_populates="balance_list")
```

### New Entity: BalanceListMember (Many-to-Many)

```python
class BalanceListMember(db.Model):
    __tablename__ = "balance_list_members"
    id = db.Column(db.Integer, primary_key=True)
    balance_list_id = db.Column(db.Integer, db.ForeignKey("balance_lists.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'owner', 'admin', 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    balance_list = db.relationship("BalanceList", back_populates="members")
    user = db.relationship("User")
    
    __table_args__ = (
        db.UniqueConstraint('balance_list_id', 'user_id', name='unique_membership'),
    )
```

### Updated Entities

**Trip (Activity)** - Link to BalanceList:
```python
# Add to Trip model:
balance_list_id = db.Column(db.Integer, db.ForeignKey("balance_lists.id"), nullable=True)
```

**Transaction** - Link to BalanceList:
```python
# Add to Transaction model:
balance_list_id = db.Column(db.Integer, db.ForeignKey("balance_lists.id"), nullable=True)
```

**SettlementSession** - Link to BalanceList:
```python
# Add to SettlementSession model:
balance_list_id = db.Column(db.Integer, db.ForeignKey("balance_lists.id"), nullable=True)
```

## API Endpoints

### Balance List CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/balance-lists` | Get all balance lists for current user |
| POST | `/balance-lists` | Create new balance list |
| GET | `/balance-lists/<id>` | Get balance list details |
| PUT | `/balance-lists/<id>` | Update balance list |
| DELETE | `/balance-lists/<id>` | Delete balance list (owner only) |

### Balance List Members

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/balance-lists/<id>/members` | Get all members of a balance list |
| POST | `/balance-lists/<id>/members` | Add member (by user_id) |
| DELETE | `/balance-lists/<id>/members/<user_id>` | Remove member |

### Invite Flow

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/balance-lists/<id>/invite-code` | Get/regenerate invite code |
| POST | `/balance-lists/join/<invite_code>` | Join balance list via invite code |

### Scoped Endpoints

All existing endpoints that deal with transactions, balances, settlements, and activities will be scoped by `balance_list_id`:

- `GET /transactions?balance_list_id=<id>`
- `GET /balances?balance_list_id=<id>`
- `GET /settlements/suggest?balance_list_id=<id>`
- `GET /settlements/history?balance_list_id=<id>`
- `GET /activities?balance_list_id=<id>`

## Request/Response Examples

### Create Balance List
```json
POST /balance-lists
{
  "name": "Vakantie Griekenland 2026",
  "currency": "EUR"
}

Response:
{
  "id": 1,
  "name": "Vakantie Griekenland 2026",
  "currency": "EUR",
  "invite_code": "abc123def456",
  "created_by": { "id": 1, "name": "Arjan" },
  "member_count": 1
}
```

### Get My Balance Lists
```json
GET /balance-lists

Response:
[
  {
    "id": 1,
    "name": "Vakantie Griekenland 2026",
    "currency": "EUR",
    "member_count": 3,
    "total_transactions": 45,
    "total_amount": 1234.56,
    "my_balance": -42.50,
    "created_at": "2026-02-15T10:30:00Z"
  },
  {
    "id": 2,
    "name": "Huishouden",
    "currency": "EUR",
    "member_count": 2,
    "total_transactions": 128,
    "total_amount": 4567.89,
    "my_balance": 150.00,
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

### Join via Invite Code
```json
POST /balance-lists/join/abc123def456

Response:
{
  "status": "success",
  "balance_list": {
    "id": 1,
    "name": "Vakantie Griekenland 2026",
    "currency": "EUR"
  }
}
```

## Frontend Components

### New Components

1. **BalanceListsView.vue** - First screen after login showing all balance lists
2. **BalanceListCard.vue** - Card component showing balance list summary
3. **BalanceListModal.vue** - Modal for creating/editing balance lists
4. **InviteModal.vue** - Modal showing invite link and QR code

### Updated Components

1. **App.vue** - Add balance list selection state
2. **Router** - Add routes for balance list views
3. **appStore.ts** - Add balance list state and actions

## UI Flow

```
Login → BalanceListsView (My Balance Lists)
           ↓
      Select Balance List
           ↓
      Main App (scoped to selected balance list)
           - Activities
           - Transactions  
           - Balances
           - Settlements
```

## Acceptance Criteria

- [ ] Model + API: BalanceList with name, currency, invite_code
- [ ] Model + API: Many-to-many User ↔ BalanceList relationship
- [ ] Model + API: Join via invite_code
- [ ] First screen = my balance lists (name, currency, member count, my balance)
- [ ] Click on balance list → existing flow scoped to that list
- [ ] Per balance list: invite link + QR code
- [ ] Invite link adds user to balance list (after login/registration)

## Migration Strategy

1. Create new tables (balance_lists, balance_list_members)
2. Add balance_list_id column to transactions, trips, settlement_sessions
3. Create a "Default" balance list for existing data
4. Migrate existing users as members of the default list
5. Assign existing transactions/activities to the default list
