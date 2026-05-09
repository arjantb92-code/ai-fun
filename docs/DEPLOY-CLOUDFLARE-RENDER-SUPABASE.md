# Deploy: Cloudflare Pages (frontend) + Render (backend) + Supabase (DB)

## Overzicht

- **Frontend (Vue)**: Cloudflare Pages (gratis)
- **Backend (Flask)**: Render free tier (slaapt na 15 min)
- **DB**: Supabase (al in gebruik)
- **Migrations**: handmatig of via Render build tegen Supabase

---

## 1. Supabase

- Project en database bestaan al.
- Noteer **Connection string** (Transaction pooler 6543) en **Direct** (5432) voor migrations.
- In Supabase Dashboard → Settings → API: gebruik de **Project URL** niet voor de DB; voor DB gebruik je de connection strings uit Database → Connection string.

---

## 2. Render – Backend (Flask)

1. **Account**: [render.com](https://render.com) → Sign up (GitHub).

2. **New → Web Service**: koppel je GitHub-repo.

3. **Instellingen**:
   - **Name**: bijv. `better-wbw-api`
   - **Region**: Frankfurt (EU) of dichtbij.
   - **Branch**: `main` (of je deploy-branch).
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**:  
     `pip install -r requirements.txt`
   - **Start Command**:  
     `gunicorn -b 0.0.0.0:$PORT app:app`

4. **Environment Variables** (Render Dashboard → Environment):
   - `PORT` = `10000` (voorkomt "New primary port detected" restart-loop; Render gebruikt 10000 als default).
   - `DATABASE_URL` = Supabase connection string (pooler, poort 6543)
   - `DIRECT_URL` = Supabase direct connection (poort 5432)
   - `SECRET_KEY` = **sterke random string, min. 32 tekens** (bijv. `openssl rand -hex 32`). Zonder dit weigert de app te starten in productie.
   - `FRONTEND_URL` = je Cloudflare Pages URL (zie stap 3), bijv. `https://jouw-project.pages.dev` (geen trailing slash). Voor CORS.
   - (optioneel) `FLASK_ENV` = `production`
   - (optioneel) **Rate limit storage**: Zet `REDIS_URL` of `RATELIMIT_STORAGE_URL` (bijv. van een Render Redis-add-on) om de in-memory limiter-warning te vermijden. Zonder Redis blijft limiter in-memory (ok voor één instance).

4b. **Health Check** (Render Dashboard → Settings → Health Check Path):
   - Zet op `/` zodat Render GET / gebruikt (de app heeft daar een `{"status":"ok"}` endpoint). Anders kan Render de service ten onrechte als unhealthy zien en herstarten.

5. **Deploy**: Save → Render bouwt en start de service.  
   - URL wordt iets als: `https://better-wbw-api.onrender.com`  
   - Noteer deze URL; die gebruik je als API-URL voor de frontend.

6. **Migrations op Supabase** (eenmalig of na schema-wijzigingen):
   - Lokaal: zet in `.env` tijdelijk `DATABASE_URL` en `DIRECT_URL` op Supabase, run:
     `./scripts/migrate-upgrade.sh`
   - Of op Render: in Build Command tijdelijk toevoegen:
     `pip install -r requirements.txt && flask db upgrade`  
     (vereist dat `FLASK_APP=app.py` en beide URLs gezet zijn; daarna Build Command weer alleen pip install.)

---

## 3. Cloudflare Pages – Frontend (Vue/Vite)

1. **Account**: [dash.cloudflare.com](https://dash.cloudflare.com) → Pages.

2. **Create project → Connect to Git**: kies je repo.

3. **Build configuratie**:
   - **Project name**: bijv. `better-wbw`
   - **Production branch**: `main`
   - **Framework preset**: Vite
   - **Build command**: `cd frontend && npm ci && npm run build`
   - **Build output directory**: `frontend/dist`

4. **Environment variables** (Settings → Environment variables):
   - **Variable name**: `VITE_API_URL`
   - **Value**: je Render backend-URL, bijv. `https://better-wbw-api.onrender.com` (geen trailing slash)
   - Scope: Production (en evt. Preview als je dezelfde API wilt).

5. **Save and Deploy**: eerste build draait.  
   - Live URL: `https://<project>.pages.dev` (of je eigen domein als je die koppelt).

6. **FRONTEND_URL op Render**:  
   Zet in Render bij Environment `FRONTEND_URL` op deze Pages-URL (bijv. `https://better-wbw.pages.dev`), dan staat CORS goed. Daarna eventueel opnieuw deployen.

---

## 4. Checklist na deploy

- [ ] Frontend opent op `https://<project>.pages.dev`.
- [ ] Login/register: requests gaan naar Render-URL (Network tab in DevTools).
- [ ] Render free tier: eerste request na ~15 min inactiviteit kan 30–60 s duren (cold start). Gebruik `scripts/wake-render-services.sh` om de backend periodiek te wekken.
- [ ] **Trage “restart”**: Meestal is dit een cold start (instance was gespindown). Bij echte deploys is de traagheid vooral `pip install`; expliciet `gunicorn -w 1 -b 0.0.0.0:$PORT app:app` houdt één worker (snellere start dan meerdere).
- [ ] Supabase: data verschijnt in je project (Dashboard → Table Editor).

---

## 5. Eigen domein (optioneel)

- **Cloudflare Pages**: Custom domains → add `app.jouwdomein.nl` (CNAME naar `<project>.pages.dev).
- **Render**: Custom domain kan ook; dan moet je op Pages `VITE_API_URL` aanpassen naar dat domein als je de API daaronder wilt.

---

## 6. Beveiliging (ingebouwd)

- **SECRET_KEY**: In productie (bij `DATABASE_URL` of `FLASK_ENV=production`) moet een sterke key van ≥32 tekens gezet zijn.
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` worden op alle responses gezet.
- **CORS**: Alleen de `FRONTEND_URL`-origin is toegestaan als die gezet is.
- **Login**: Rate limit 10 pogingen per minuut per IP; generiek foutbericht ("Invalid"); veilige input-validatie.
- **JWT**: 24u exp; geen gevoelige details in foutresponses.
- **Algemene API**: 300 requests/minuut per IP (Flask-Limiter).

---

## 7. Snelle referentie

| Waar        | Wat |
|------------|-----|
| Frontend   | Cloudflare Pages, build: `cd frontend && npm ci && npm run build`, output: `frontend/dist` |
| Backend    | Render, root: `backend`, start: `gunicorn -b 0.0.0.0:$PORT app:app` |
| DB         | Supabase, `DATABASE_URL` + `DIRECT_URL` op Render (en lokaal voor migrations) |
| API-URL    | `VITE_API_URL` op Pages = Render URL |
| CORS       | `FRONTEND_URL` op Render = Pages URL |
