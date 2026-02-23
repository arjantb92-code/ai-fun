# APP-41: Invite-link Login, Account via Invite, Activation, Google Sign-In

## Overview

This document specifies the implementation of invite-based registration, Google OAuth, and email activation for Better WBW.

## Problem Statement

- QR/invite links lead nowhere for non-logged-in users (only show generic login screen)
- No registration flow - new users cannot create accounts via invite
- No way to verify email addresses for account security

## Goals

1. **Invite-link/QR** → landing page with **list-preview** (name, currency) + prompt: "Log in or create account to join"
2. **Invite-only registration** (no open registration)
3. **Google Sign-In** from the start (alongside email/password)
4. **Activation flow**: First login allowed without activation; email verification required for subsequent logins

---

## Implementation

### Backend Endpoints

#### 1. Public Preview Endpoint
```
GET /balance-lists/public-preview/<invite_code>
```
- **Auth**: None required
- **Response**: `{ id, name, currency, member_count, created_by_name }`
- **Error**: 404 if invite code invalid

#### 2. Register from Invite
```
POST /auth/register-from-invite
```
- **Auth**: None required
- **Body**: `{ invite_code, name, email, password }`
- **Behavior**:
  - Validates invite code
  - Creates user with `email_verified: false`
  - Generates activation token
  - Auto-joins the balance list
  - Returns JWT for immediate first login
  - Sends activation email (TODO: implement email sending)
- **Response**: `{ token, user, balance_list, activation_url (dev only) }`

#### 3. Account Activation
```
POST /auth/activate
```
- **Auth**: None required
- **Body**: `{ token, password (optional) }`
- **Behavior**:
  - Validates activation token
  - Sets `email_verified: true`
  - Updates password if provided
  - Clears activation token
- **Response**: `{ status: "success", user }`

#### 4. Resend Activation
```
POST /auth/resend-activation
```
- **Auth**: None required
- **Body**: `{ email }`
- **Behavior**: Generates new activation token, sends email

#### 5. Google OAuth Initiation
```
GET /auth/google?invite_code=<optional>
```
- **Auth**: None required
- **Response**: `{ auth_url }` - Redirect URL for Google OAuth
- **State**: invite_code encoded in OAuth state parameter

#### 6. Google OAuth Callback
```
GET /auth/google/callback?code=<code>&state=<state>
```
- **Behavior**:
  - Exchanges code for tokens
  - Gets user info from Google
  - If existing user with matching OAuth ID → log in
  - If existing user with matching email → link accounts
  - If new user + invite_code → create account, join list
  - If new user without invite_code → return `needs_invite: true` error
- **Response**: `{ token, user }`

#### 7. Login Enhancement
```
POST /login
```
- **Change**: Now checks `email_verified` status
- **Behavior**:
  - If user has activation token but email not verified → return 403 with `requires_activation: true`
  - First login (no activation token yet) is allowed

### Database Changes

#### User Model Extensions
```python
oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', etc.
oauth_id = db.Column(db.String(255), nullable=True)  # Provider's user ID
email_verified = db.Column(db.Boolean, default=False)
activation_token = db.Column(db.String(64), nullable=True)
activation_token_expires = db.Column(db.DateTime, nullable=True)
```

#### Migration
- File: `8e9f0a1b2c3d_add_oauth_and_activation_fields.py`
- Adds all new columns
- Creates index on `(oauth_provider, oauth_id)`

### Frontend Components

#### 1. JoinLandingView (`/join/:inviteCode`)
- Shows balance list preview (name, currency, member count)
- Three action buttons:
  - **Continue with Google** - Initiates Google OAuth with invite_code
  - **Log In with Email** - Shows login form
  - **Create Account** - Shows registration form
- After login/register, auto-joins the balance list

#### 2. LoginView Updates
- Added Google Sign-In button
- Added activation-required message with resend link
- Shows help text about needing invite link

#### 3. ActivationView (`/activate?token=<token>`)
- Validates activation token
- Allows setting/updating password
- Option to activate without changing password
- Redirects to login on success

### Frontend Routes

```javascript
{
  path: '/join/:inviteCode',
  name: 'join',
  component: App
},
{
  path: '/activate',
  name: 'activate',
  component: App
}
```

### Environment Variables

Required for Google OAuth:
```
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=<your-callback-url>  # Optional, defaults to {host}/auth/google/callback
FRONTEND_URL=<frontend-url>  # For activation email links
```

---

## Activation Flow Details

### Option A: First Login Grace Period (Implemented)

1. User registers via invite → account created with `email_verified: false`
2. First login: Allowed immediately (grace period)
3. Activation email sent with token
4. User clicks link → sets password → `email_verified: true`
5. Subsequent logins: Require `email_verified: true`

### Flow Diagram

```
[Invite Link] → [JoinLandingView]
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    [Google]    [Login]    [Register]
        │            │            │
        └────────────┼────────────┘
                     ▼
            [Auto-join Balance List]
                     │
                     ▼
              [Main App View]
```

### Activation Email Flow

```
[Register] → [Send Activation Email]
                     │
                     ▼
           [User clicks link]
                     │
                     ▼
           [ActivationView]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  [Set Password]          [Skip Password]
         │                       │
         └───────────┬───────────┘
                     ▼
         [email_verified = true]
                     │
                     ▼
              [Login Page]
```

---

## Security Considerations

1. **Activation tokens** expire after 7 days
2. **Rate limiting** on sensitive endpoints:
   - `/login`: 10/minute
   - `/auth/register-from-invite`: 5/minute
   - `/auth/activate`: 10/minute
   - `/auth/resend-activation`: 3/minute
3. **OAuth state parameter** prevents CSRF attacks
4. **Google emails** are auto-verified (Google handles verification)
5. **Password requirements**: Minimum 6 characters

---

## TODO / Future Enhancements

1. [ ] Implement actual email sending (currently logs activation URL)
2. [ ] Add Apple Sign-In
3. [ ] Add password reset flow
4. [ ] Add "remember me" functionality
5. [ ] Implement proper Google ID token verification with public keys
6. [ ] Add email change flow with re-verification

---

## Testing Checklist

- [ ] Visit `/join/<code>` while logged out → shows JoinLandingView
- [ ] Register via invite → creates account, joins list, shows main view
- [ ] Login via invite page → joins list automatically
- [ ] Google Sign-In with invite → creates account if new, joins list
- [ ] Google Sign-In without invite (new user) → shows "needs invite" error
- [ ] Google Sign-In without invite (existing user) → logs in
- [ ] Second login without activation → shows "requires activation" message
- [ ] Activation link → allows setting password → verifies email
- [ ] Resend activation → generates new token
- [ ] Login after activation → works normally
