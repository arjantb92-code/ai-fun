# Ticket: Meerdere balansen per account + eerste scherm + uitnodigen

**Status:** Concept (wacht op akkoord voor Linear)  
**Type:** Feature  
**Scope:** Backend (models, API), Frontend (routing, eerste scherm, uitnodigen)

---

## Doel

- Een **account** kan aan **meerdere balansen (lijsten)** gekoppeld zijn.
- Het **eerste scherm** na login is een overzicht van “mijn balansen” (naam, valuta, deelnemers). Pas na een klik op een balans zie je de balans/transacties.
- Uitnodigen voor een balans moet **makkelijk** kunnen via **link en/of QR-code**.
- Elke balans heeft: **naam**, **valuta**, **deelnemers** (en blijft WBW-compatibel: splits, vereffening).

---

## Huidige situatie (kort)

- **Users** en **Trip** (Activity) bestaan; er is geen “groep” of “balanslijst” als eerste-laag concept.
- Balansen worden nu per activity berekend; users zijn globaal (`is_group_member`).
- Eerste scherm is nu activity/transactie-gericht, niet “kies een balans”.

Zie: `backend/models.py` (User, Trip, Transaction, TransactionSplit, SettlementSession), `docs/PINIA_AUDIT.md`, `.cursorrules` (WBW splits + settlement).

---

## Gewenste situatie

1. **Balans (lijst)** = eerste-laag concept  
   - Eigenschappen: **naam**, **valuta** (bijv. EUR, USD), **deelnemers** (users die bij deze balans horen).
2. **Account ↔ balansen**  
   - Een user kan in meerdere balansen zitten (many-to-many).
3. **Eerste scherm na login**  
   - Overzicht “Mijn balansen”: lijst met per balans o.a. naam, valuta, deelnemers. Geen balans/transacties zichtbaar tot je op een rij klikt.
4. **Na klik op een balans**  
   - Bestaande flow (transacties, balans, vereffening) maar dan **scoped op die balans**. WBW-logica (splits, gewichten, minimalisatie transacties) blijft gelden binnen die balans.
5. **Uitnodigen**  
   - Per balans: uitnodigings-**link** en **QR-code** waarmee iemand (eventueel na registratie/login) bij die balans wordt toegevoegd.

---

## Data model (voorstel)

- **BalanceList** (of `Group`):  
  - `id`, `name`, `currency` (string, bijv. `EUR`), `invite_code` (uniek, voor link/QR), `created_at`, `owner_id` (FK User) optioneel.
- **BalanceListMember** (user ↔ balans, many-to-many):  
  - `balance_list_id`, `user_id`, rol indien nodig (bijv. admin).
- **Trip/Activity** koppelen aan balans:  
  - `trip.balance_list_id` (FK naar BalanceList). Bestaande Trip/Transaction/Settlement-logica blijft; scope wordt “binnen deze balans”.
- **User** blijft zoals nu; geen “global group” meer nodig voor WBW-scope: scope = balans.

Uitnodigingslink: bijv. `/{base}/join/{invite_code}` of `?invite=CODE`. QR-code = zelfde URL.

---

## UX (kort)

| Stap | Wat |
|------|-----|
| 1 | Login → **eerste scherm: “Mijn balansen”** (lijst met naam, valuta, deelnemers). |
| 2 | Klik op een balans → **detail: balans + transacties/activiteiten** (bestaande flows, nu per balans). |
| 3 | Uitnodigen: knop “Nodig uit” → toon **link + QR-code**; kopieer link / toon QR. |
| 4 | Nieuwe user opent link (of scant QR) → **join-flow**: registreren/login + toevoegen aan die balans. |

---

## WBW-aansluiting

- Transacties en splits blijven **per balans** (via Trip/Activity die aan een balans hangen).  
- Settlement (vereffening) blijft binnen de **deelnemers van die balans**; bestaande “minimaliseer aantal transacties”-logica ongewijzigd toepassen binnen die set.  
- Gewichten (splits) blijven ondersteund zoals in `.cursorrules`.

---

## Acceptatiecriteria

- [ ] Model: BalanceList (naam, valuta, invite_code) + BalanceListMember; Trip gekoppeld aan BalanceList.
- [ ] API: CRUD balansen, join via invite_code, lijst “mijn balansen” voor ingelogde user.
- [ ] Eerste scherm na login = “Mijn balansen” (naam, valuta, deelnemers per rij).
- [ ] Klik op een balans opent de bestaande balans/transactie-flow, nu scoped op die balans.
- [ ] Per balans: uitnodigingslink + QR-code; link werkt (na login/registratie) om user aan balans toe te voegen.
- [ ] Bestaande WBW-logica (splits, settlement) werkt binnen een gekozen balans.

---

## Technische notities

- **Migraties:** nieuwe tabellen + `trip.balance_list_id` (of gelijkwaardig); bestaande data: één default BalanceList aanmaken en huidige trips daaraan koppelen.
- **Frontend:** routing aanpassen (eerste route na login = balansoverzicht); store/state uitbreiden voor “huidige balans” en “mijn balansen” (zie PINIA_AUDIT voor store-aanbevelingen).
- **Invite:** `invite_code` uniek, voldoende lang/random; rate limiting op join-endpoint (zie bestaande limiter).

---

## Linear (na akkoord)

- **Titel:** `Feature: Meerdere balansen per account, eerste scherm + uitnodigen link/QR`
- **Description:** Kopieer de inhoud van dit document (of de secties Doel t/m Acceptatiecriteria).
- **Labels:** feature, backend, frontend, wbw.

**In Linear zetten na akkoord:**

1. **Handmatig:** Linear → New issue → bovenstaande titel + description (of kopieer uit dit doc).
2. **Via script:** `python scripts/create_linear_ticket_balance_lists.py` (vereist `LINEAR_API_KEY` in `.env`; optioneel `LINEAR_TEAM_ID`).
