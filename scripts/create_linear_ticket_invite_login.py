#!/usr/bin/env python3
"""
Maakt één Linear issue aan: Invite-link login, account via invite, activatie, Google Sign-In.
Run na akkoord op het ticket in docs/TICKET-INVITE-LOGIN-ACTIVATION.md.

Usage:
    python scripts/create_linear_ticket_invite_login.py

Vereist: LINEAR_API_KEY (en optioneel LINEAR_TEAM_ID) in .env
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")

if not LINEAR_API_KEY:
    print("❌ LINEAR_API_KEY niet gevonden in .env")
    sys.exit(1)

TITLE = "Feature: Invite-link login, account via invite, activatie, Google Sign-In"
DESCRIPTION = """## Probleem
- QR / uitnodigingslink leiden nergens toe voor niet-ingelogde users (alleen generiek inlogscherm).
- Geen registratie; nieuwe users kunnen niet via invite een account aanmaken.

## Doel
1. **Invite-link/QR** → pagina met **lijst-preview** (naam, valuta) + blokkade: "Log in of maak account om mee te doen."
2. **Alleen via invite** account aanmaken (geen open registratie).
3. **Google Sign-In** vanaf het begin (naast e-mail/wachtwoord).
4. **Activatie:** eerste keer mag zonder activatie; daarna e-mail activeren. Activeren = wachtwoord instellen zodat je weer kunt inloggen.

## Acceptatiecriteria (kort)
- Public endpoint: GET /balance-lists/public-preview/<invite_code> (geen auth).
- Invite-landing op /join/:inviteCode: preview + Inloggen | Account aanmaken (invite-only signup).
- POST /auth/register-from-invite (invite_code verplicht); na registratie direct join + eerste login; activatie-mail voor volgende logins.
- Google OAuth: backend /auth/google + callback; User oauth_provider/oauth_id; knoppen op login + invite-landing; state met invite_code.
- Activatie-flow (Optie A): eerste keer direct inlog; activatie-mail; link → wachtwoord instellen + email_verified; volgende logins alleen als email_verified.

Volledige specificatie (incl. activatie-opties, Google-checklist): docs/TICKET-INVITE-LOGIN-ACTIVATION.md"""


def get_team_id():
    if LINEAR_TEAM_ID:
        return LINEAR_TEAM_ID
    import requests
    query = """
    query { teams { nodes { id name } } }
    """
    r = requests.post(
        "https://api.linear.app/graphql",
        json={"query": query},
        headers={"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    teams = data.get("data", {}).get("teams", {}).get("nodes", [])
    if not teams:
        print("❌ Geen teams gevonden")
        sys.exit(1)
    if len(teams) == 1:
        return teams[0]["id"]
    print("Kies een team (nummer):")
    for i, t in enumerate(teams, 1):
        print(f"  {i}. {t['name']}")
    n = input("Nummer: ").strip()
    idx = int(n) - 1
    if 0 <= idx < len(teams):
        return teams[idx]["id"]
    sys.exit(1)


def create_issue(team_id: str) -> None:
    import requests
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier title url }
      }
    }
    """
    variables = {
        "input": {
            "teamId": team_id,
            "title": TITLE,
            "description": DESCRIPTION,
        }
    }
    r = requests.post(
        "https://api.linear.app/graphql",
        json={"query": mutation, "variables": variables},
        headers={"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"},
        timeout=10,
    )
    r.raise_for_status()
    out = r.json()
    if out.get("data", {}).get("issueCreate", {}).get("success"):
        issue = out["data"]["issueCreate"]["issue"]
        print(f"✓ Issue aangemaakt: {issue['identifier']} – {issue['title']}")
        print(f"  URL: {issue.get('url', '')}")
    else:
        print("❌ Aanmaken mislukt:", out.get("errors", out))


if __name__ == "__main__":
    team_id = get_team_id()
    create_issue(team_id)
