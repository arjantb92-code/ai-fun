# Draft: Better WBW (Web App MVP)

## Requirements (Confirmed)
- **Core Goal**: A "Better WBW" (Wie Betaalt Wat) - Group Expense Splitting Tool.
- **Workflow**: 
  1. Import Bank Transactions (CSV/Bank Export).
  2. Select relevant transactions (filter personal vs group).
  3. Assign/Split costs (Who participated?).
  4. Calculate Balance (Who owes who).
- **Key Feature**: Add receipts (Bonnetjes) with **OCR/Recognition**.
- **Platform**: Web App first (Vue.js), then Desktop/App.
- **Stack**: 
  - Frontend: Vue.js ("TrainMore" style - Industrial/Urban).
  - Backend: Python Flask.
  - Database: PostgreSQL (Local first).
- **Design Style**: "TrainMore" (Industrial, bold, black/neon, high energy).
- **Deployment**: Local hosting first.
- **Automation**: Not tax-based. Goal: "Fair distribution of who paid what".

## Technical Decisions
- **Secrets**: Must generate and provide local keys/credentials.
- **OCR**: Python-based local OCR for receipts (TBD: Tesseract vs EasyOCR).
- **Algorithm**: Debt simplification (minimize transactions between participants).

## Research Findings (Internal Knowledge)
- **Design Inspiration (TrainMore)**: 
  - **Palette**: Dark Mode default (Jet Black #000000 / Charcoal #1A1A1A).
  - **Accents**: Neon Green/Volt or Stark White. High contrast.
  - **Typography**: Bold, industrial sans-serif (e.g., Oswald, Roboto Condensed).
  - **Vibe**: "No excuses", clean, direct, performance-oriented.
- **WBW Algorithm**: 
  - Logic: Calculate net balance (Paid - FairShare). Match Max Debtor with Max Creditor recursively.
  - Implementation: Custom Python logic (graph theory: debt simplification).
- **OCR Choice**: `pytesseract` (Tesseract) for MVP.
  - Pros: Local, free, lightweight.
  - Cons: Needs clear images.
  - Fallback: Manual entry if OCR fails.

## Scope Boundaries
- **INCLUDE**: 
  - Dashboard with "TrainMore" dark aesthetic.
  - Receipt upload + basic OCR (Date/Amount).
  - CSV Import (Generic format first).
  - Group balance calculation.
- **EXCLUDE**:
  - Live Bank API connections (PSD2).
  - Complex tax rules (BTW logic).
  - Mobile App (Native) - strictly Web App (PWA) for now.

## Open Questions
- **Bank Format**: Which bank(s) specifically? (ING, Rabo, ABN?). Parsing logic differs per bank.
