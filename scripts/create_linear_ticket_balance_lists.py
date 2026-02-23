#!/usr/bin/env python3
"""
Maakt één Linear issue aan: Meerdere balansen per account + eerste scherm + uitnodigen.
Run na akkoord op het ticket in docs/TICKET-MULTIPLE-BALANCE-LISTS.md.

Usage:
    python scripts/create_linear_ticket_balance_lists.py

Vereist: LINEAR_API_KEY (en optioneel LINEAR_TEAM_ID) in .env
"""

import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")

if not LINEAR_API_KEY:
    print("❌ LINEAR_API_KEY niet gevonden in .env")
    sys.exit(1)

# Inline description (korte versie voor Linear)
TITLE = "Feature: Meerdere balansen per account, eerste scherm + uitnodigen link/QR"
DESCRIPTION = """## Doel
- Account gekoppeld aan **meerdere balansen** (lijsten met naam, valuta, deelnemers).
- **Eerste scherm** na login = overzicht "Mijn balansen"; klik op een balans → balans/transacties.
- **Uitnodigen** via link en/of QR-code per balans.

## Data model (kort)
- Nieuwe entiteit BalanceList (naam, valuta, invite_code); many-to-many User ↔ BalanceList.
- Trip/Activity koppelen aan BalanceList. WBW (splits, settlement) blijft binnen balans.

## Acceptatiecriteria
- Model + API: BalanceList, members, join via invite_code.
- Eerste scherm = mijn balansen (naam, valuta, deelnemers).
- Klik op balans → bestaande flow scoped op die balans.
- Per balans: uitnodigingslink + QR; link voegt user toe aan balans (na login/registratie).

Volledige specificatie: zie docs/TICKET-MULTIPLE-BALANCE-LISTS.md in de repo."""


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
