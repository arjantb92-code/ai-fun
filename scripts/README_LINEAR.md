# Linear Import Script - Better WBW

Dit script importeert automatisch alle milestones en tickets in Linear voor het Better WBW project.

## Setup

### 1. Linear API Key ophalen

1. Ga naar: https://linear.app/settings/api
2. Klik op "Create API Key"
3. Geef het een naam (bijv. "Better WBW Import")
4. Kopieer de API key

### 2. API Key toevoegen aan .env

Voeg toe aan je `.env` bestand in de root:

```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
LINEAR_TEAM_ID=optional_team_id_here  # Optioneel, script vraagt erom als niet gezet
```

### 3. Dependencies installeren

Het script gebruikt `requests` en `python-dotenv`. Check of ze geïnstalleerd zijn:

```bash
pip install requests python-dotenv
```

Of voeg toe aan `backend/requirements.txt` als je ze daar wilt hebben.

## Gebruik

```bash
# Vanuit project root
python scripts/import_linear.py
```

Het script zal:
1. Je Linear team selecteren (als LINEAR_TEAM_ID niet is gezet)
2. Een project "Better WBW" aanmaken
3. Alle milestones aanmaken
4. Alle tickets aanmaken en koppelen aan milestones

## Wat wordt aangemaakt?

- **Project**: Better WBW
- **4 Milestones**:
  - Core Foundation & Auth (MVP)
  - Transactie Beheer & Balans
  - Import & AI Integraties
  - UI Polish & Hosting (TrainMore Style)
  - Backlog / Nice-to-haves
- **13 Tickets** met prioriteiten en beschrijvingen

## Troubleshooting

### "LINEAR_API_KEY not found"
- Check of de key in `.env` staat
- Check of `.env` in de root van het project staat

### "No teams found"
- Maak eerst een team aan in Linear
- Of zet LINEAR_TEAM_ID handmatig in `.env`

### "Project creation failed"
- Project bestaat mogelijk al
- Script probeert het bestaande project te gebruiken

## Handmatige import (alternatief)

Als het script niet werkt, kun je ook handmatig importeren:

1. Ga naar Linear → Projects → New Project
2. Naam: "Better WBW"
3. Maak milestones aan voor elke sectie
4. Maak issues aan en koppel aan milestones

De structuur staat in `scripts/import_linear.py` in de `PROJECT_STRUCTURE` variabele.
