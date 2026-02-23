# Invite-link login, account aanmaken via invite, activatie & Google Sign-In

**Linear (optional):** Zie titel/omschrijving hieronder. Script: `python scripts/create_linear_ticket_invite_login.py` (vereist `LINEAR_API_KEY` in .env).

---

## Probleem

- **QR-code / uitnodigingslink** (`/join/:inviteCode`) leiden nu nergens toe voor niet-ingelogde gebruikers: ze zien alleen het algemene inlogscherm, zonder context over welke lijst ze joinen.
- Er is **geen registratie**: alleen inloggen met bestaand account. Nieuwe gebruikers kunnen niet via de invite een account aanmaken.
- **Lookup** van een balance list op invite code vereist nu een token (`GET /balance-lists/lookup/<invite_code>` is `@token_required`), dus je kunt de lijst niet eens tonen zonder ingelogd te zijn.

## Doel

1. **Invite-link / QR** → gebruiker komt op een pagina waar de **lijst zichtbaar is** (preview: naam, valuta, evt. aantal leden), met een **blokkade**: "Log in of maak een account om mee te doen."
2. **Alleen via invite** kan iemand een account aanmaken (geen open registratie elders).
3. Op die pagina: **Inloggen** of **Account aanmaken** (beide in context van de invite).
4. **Google Sign-In** vanaf het begin meenemen naast e-mail/wachtwoord.
5. **Activatie** gebruiksvriendelijk: eerste keer mag zonder activatie; daarna moet e-mail geactiveerd zijn. **Activeren = wachtwoord kunnen zetten/gebruiken** zodat je later opnieuw kunt inloggen (zonder activatie kun je niet nog een keer inloggen).

---

## 1. Invite-flow (frontend + backend)

### Huidige flow (kort)

- Route: `/join/:inviteCode` → zelfde `App.vue`; als niet ingelogd → alleen `LoginView` (geen invite-context). Als wel ingelogd → `handleJoinFromUrl` voert join uit.
- Lookup: `GET /balance-lists/lookup/<invite_code>` vereist token → ongeschikt voor anonieme preview.

### Gewenste flow

1. Gebruiker opent **link of scant QR** → `https://<origin>/join/<invite_code>`.
2. **Zonder token**: toon een **Invite-landing**:
   - **Public lookup** van de balance list (alleen basisinfo: naam, valuta, member_count). Geen gevoelige data.
   - Tekst zoals: "Je bent uitgenodigd voor **&lt;naam lijst&gt;** – log in of maak een account om mee te doen."
   - Knoppen: **Inloggen** | **Account aanmaken** (beide behouden `invite_code` in state/URL).
3. **Inloggen** → bestaand `LoginView` (evt. met invite_code in URL/state) → na succes → join balance list + redirect naar lijst (bestaande `handleJoinFromUrl`).
4. **Account aanmaken** → alleen beschikbaar op deze pagina (invite-only signup). Na aanmaak → (afhankelijk van activatie-keuze) direct join + inloggen, of eerst "Controleer je e-mail om je account te activeren".

### Backend

- **Nieuwe endpoint (public):**  
  `GET /balance-lists/public-preview/<invite_code>`  
  - Geen `@token_required`.  
  - Response: `{ "id", "name", "currency", "member_count" }` of 404.  
  - Geen lijst van leden of andere privé-informatie.
- Bestaande `POST /balance-lists/join/<invite_code>` blijft token verplicht (na inlog/registratie).

---

## 2. Registratie (alleen via invite)

- **Geen** algemene "Registreren"-link op de hoofdpagina; alleen "Inloggen".
- **Wel** "Account aanmaken" op de invite-landing (`/join/:inviteCode`), met invite_code verplicht in het request.
- Backend:
  - **Nieuwe endpoint:** bv. `POST /auth/register-from-invite`  
    Body: `{ "invite_code", "name", "email", "password" }` (of zonder password bij magic-link flow).  
    - Valideer dat `invite_code` bestaat.  
    - Maak user aan (email uniek; bij duplicate: foutmelding of "log in").  
    - Optioneel: direct lid maken van de balance list (join) na succesvolle aanmaak.  
    - Return JWT + user (als eerste keer zonder activatie) OF stuur activatie-mail en return `{ "message": "Check your email to activate" }` (als activatie verplicht na eerste keer).
- Frontend: formulier "Account aanmaken" op invite-landing met naam, e-mail, wachtwoord (en evt. "Login met Google"); na submit → bovenstaande API.

---

## 3. Google Sign-In – wat ervoor nodig is

### Google Cloud

1. **Google Cloud Console** – project aanmaken (of bestaand).
2. **OAuth 2.0 Client** – type "Web application":
   - **Authorized JavaScript origins:**  
     `http://localhost:5173` (of jouw dev port), `https://<productie-domein>`
   - **Authorized redirect URIs:**  
     Backend callback URL, bv. `https://<api>/auth/google/callback` (lokaal: `http://localhost:5000/auth/google/callback`).
3. **OAuth consent screen** – app naam, support e-mail, test users indien "Testing".
4. **Credentials** – Client ID + Client Secret (secret alleen op backend).

### Backend (Flask)

- **Optie A – Flask-Dance**  
  `pip install flask-dance[google]`  
  - Vooraf geconfigureerde blueprint voor Google; redirect naar Google, callback afhandelen, token uitwisselen.  
  - Na callback: Google user info ophalen (email, name, sub/id). User opzoeken of aanmaken; JWT uitgeven.
- **Optie B – Handmatig**  
  - Redirect URL bouwen (client_id, redirect_uri, scope, state).  
  - Endpoint `/auth/google/callback`: code ontvangen, exchange voor tokens, userinfo ophalen.  
  - Zelfde logica: find-or-create user, JWT.

**User-model uitbreiding (voor Google):**

- `oauth_provider` (nullable string), bv. `'google'`.
- `oauth_id` (nullable string), bv. Google `sub`.
- `password_hash` blijft nullable (Google-users hebben geen wachtwoord).
- Bij "Login met Google" op invite-pagina: na callback kan de user direct worden toegevoegd aan de balance list (zelfde join-flow als bij e-mail-login).

### Frontend

- Knop "Inloggen met Google" / "Account aanmaken met Google":
  - Redirect naar backend-URL die de redirect naar Google start (bijv. `GET /auth/google`), met `state` waarin je `invite_code` meeneemt (base64 of signed param), zodat na callback de join kan worden afgehandeld.
- Geen client-side Google Client ID nodig als je de hele OAuth-flow via de backend laat lopen (aanbevolen voor security).

### Korte checklist Google

- [ ] Google Cloud project + OAuth client (Web application).
- [ ] Redirect URIs en origins correct.
- [ ] Backend: `/auth/google` (start) + `/auth/google/callback` (code → token → userinfo, find-or-create user, JWT).
- [ ] User model: `oauth_provider`, `oauth_id`; `password_hash` nullable.
- [ ] Frontend: knoppen "Inloggen met Google" / "Account aanmaken met Google" op login- en invite-landing, met invite in state.

---

## 4. Activatie – opties en aanbeveling

Eis: **Eerste keer mag zonder activatie; daarna moet e-mail geactiveerd zijn. Activeren = wachtwoord kunnen zetten/gebruiken** zodat je opnieuw kunt inloggen.

### Optie A – Eerste login zonder activatie, daarna e-mail verplicht

- **Eerste registratie:** Account aanmaken → direct inloggen (JWT) + join lijst. Geen mail. User kan direct gebruiken.
- **Voor volgende login:** E-mail moet "geverifieerd" zijn. Bij eerste registratie een **activatie-mail** sturen met link. Klik op link → "Stel je wachtwoord in" (of "Bevestig e-mail" en daarna apart wachtwoord instellen). Na activatie: `email_verified = true`; user kan altijd inloggen met e-mail + wachtwoord.
- **Zonder activatie:** Na eerste sessie (token verlopen) kan user niet opnieuw inloggen tot activatie gedaan is. Duidelijke melding: "Controleer je e-mail om je account te activeren en een wachtwoord in te stellen."

**Voordelen:** Lage drempel eerste keer; duidelijke reden om te activeren (opnieuw inloggen).  
**Nadeel:** Eén sessie mogelijk zonder geverifieerde e-mail (acceptabel als alleen via invite).

### Optie B – Magic link eerste keer, daarna wachtwoord

- Registratie: alleen e-mail (geen wachtwoord). Stuur **magic link**; klik → ingelogd + "Kies een wachtwoord voor volgende keren". Daarna `email_verified = true` + password_hash gezet.
- Volgende keren: inloggen met e-mail + wachtwoord (of Google).

**Voordelen:** Geen wachtwoord vergeten bij eerste keer; e-mail wordt per definitie geverifieerd.  
**Nadelen:** Extra stap (mail openen); magic-link endpoint en token-beveiliging nodig.

### Optie C – Altijd eerst activatie (strenger)

- Na aanmelding geen directe login; alleen mail: "Activeer je account". Link → wachtwoord instellen → dan pas inloggen.
- **Nadeel:** Meer friction voor eerste keer; jij gaf aan dat eerste keer mag zonder activatie.

### Aanbeveling

**Optie A** sluit het beste aan bij je wens: eerste keer direct gebruik, daarna activatie verplicht om opnieuw in te loggen; activatie = wachtwoord krijgen/kiezen.

**Implementatie (kort):**

- User model: `email_verified` (boolean, default False). Na activatie True.
- Na eerste registratie: direct JWT + join; op de achtergrond **activatie-mail** sturen met link naar bv. `/auth/activate?token=<signed_token>`.
- Activatie-endpoint (GET of POST): token valideren → toon (of API voor) "Kies wachtwoord" → sla password_hash op, zet `email_verified = True`.
- Login (e-mail/wachtwoord): alleen toestaan als `email_verified` True; anders 401 met message "Activeer eerst je account via de link in je e-mail".
- (Optioneel) "Verstuur activatielink opnieuw" voor niet-geverifieerde users.

---

## 5. Samenvatting acceptatiecriteria

- [ ] **Public preview:** `GET /balance-lists/public-preview/<invite_code>` (geen auth) retourneert naam, valuta, member_count.
- [ ] **Invite-landing** op `/join/:inviteCode`: voor niet-ingelogde users toon lijst-preview + "Log in of maak account" + knoppen Inloggen / Account aanmaken; invite_code blijft in URL/state.
- [ ] **Registratie alleen via invite:** "Account aanmaken" alleen op invite-landing; backend `POST /auth/register-from-invite` met invite_code verplicht.
- [ ] **Inloggen** op invite-landing: na succes join uitvoeren en naar lijst (bestaande flow uitbreiden met invite-context).
- [ ] **Google Sign-In:** Backend OAuth-flow (start + callback); User model met oauth_provider/oauth_id; knoppen op login- en invite-landing; state bevat invite_code voor join na callback.
- [ ] **Activatie (Optie A):** Eerste registratie → direct inlog + join; activatie-mail met link; activatie = wachtwoord instellen + `email_verified = True`; volgende logins e-mail/wachtwoord alleen als `email_verified`; duidelijke foutmelding als niet geactiveerd.
- [ ] QR-code en invite-link leiden naar bovenstaande invite-landing en gedragen zich gebruiksvriendelijk (lijst zichtbaar, duidelijke CTA’s).

---

## 6. Technische notities

- **Lookup:** Huidige `GET /balance-lists/lookup/<invite_code>` kan blijven voor ingelogde users (meer velden/`is_member`); public preview is een aparte, open endpoint.
- **State bij OAuth:** `state` parameter moet `invite_code` (en evt. nonce) bevatten; na callback parse state en voer join uit als code aanwezig.
- **Mail:** Voor activatie-mails: SMTP of transactionele provider (SendGrid, Resend, etc.); template met link naar frontend `/auth/activate?token=...` die frontend naar backend `POST /auth/activate` met token + nieuw wachtwoord stuurt (of GET met token en toon form).
- **Security:** Activatie-token: signed (JWT of HMAC), korte geldigheid (bijv. 24u), één keer te gebruiken; rate limiting op register en activate.
