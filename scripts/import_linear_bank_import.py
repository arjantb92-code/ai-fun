#!/usr/bin/env python3
"""
Linear Import Script - Better WBW Bank Import Flow

Voegt alleen een extra milestone + tickets toe voor de bank-import preview/commit-flow,
zonder de bestaande structuur te dupliceren.

Usage:
    python scripts/import_linear_bank_import.py
"""

from typing import Dict, Optional

from import_linear import (  # type: ignore
    LINEAR_API_KEY,
    PROJECT_STRUCTURE,
    linear_query,
    get_team_id,
    create_milestone,
    create_issue,
)


def get_project_id(team_id: str) -> Optional[str]:
    """Zoek het bestaande 'Better WBW' project op basis van naam."""
    import sys
    
    # Probeer eerst via projects query (werkt vaak beter)
    query = """
    query {
      projects(first: 50) {
        nodes {
          id
          name
          teams {
            nodes {
              id
            }
          }
        }
      }
    }
    """
    try:
        result = linear_query(query)
        
        # Check voor GraphQL errors
        if "errors" in result:
            print(f"⚠️  GraphQL errors: {result['errors']}")
            # Fall through naar fallback
        
        projects = result.get("data", {}).get("projects", {}).get("nodes", [])
        
        # Filter op project naam EN team
        for p in projects:
            if p.get("name") == PROJECT_STRUCTURE["name"]:
                # Check of dit project bij het team hoort
                team_ids = [t.get("id") for t in p.get("teams", {}).get("nodes", [])]
                if team_id in team_ids:
                    return p.get("id")
        
        # Als niet gevonden, probeer fallback via team query
        query_fallback = """
        query($teamId: ID!) {
          team(id: $teamId) {
            projects {
              nodes {
                id
                name
              }
            }
          }
        }
        """
        try:
            result = linear_query(query_fallback, {"teamId": team_id})
            
            if "errors" in result:
                print(f"⚠️  GraphQL errors (fallback): {result['errors']}")
                return None
            
            projects = (
                result.get("data", {})
                .get("team", {})
                .get("projects", {})
                .get("nodes", [])
            )
            for p in projects:
                if p.get("name") == PROJECT_STRUCTURE["name"]:
                    return p.get("id")
            return None
        except Exception as e2:
            print(f"⚠️  Fallback query faalde: {e2}")
            return None
            
    except Exception as e:
        print(f"⚠️  Fout bij ophalen projecten: {e}")
        # Print response details als beschikbaar
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text[:200]}")
        return None


def main() -> None:
    print("🚀 Linear Import - Bank Import Flow\n")

    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY niet gevonden in .env")
        print("   Zet LINEAR_API_KEY=... in je .env bestand.")
        return

    # 1. Team kiezen
    team_id = get_team_id()

    # 2. Project-ID ophalen (probeer automatisch, anders handmatig)
    print(f"\n🔍 Zoeken naar project: {PROJECT_STRUCTURE['name']}...")
    project_id = get_project_id(team_id)
    
    if not project_id:
        print("\n⚠️  Project niet automatisch gevonden.")
        print(
            "Plak de project ID (UUID) van je bestaande 'Better WBW' project hier.\n"
            "Tip: open het project in Linear, druk Cmd/Ctrl+K en kies 'Copy model UUID'."
        )
        project_id = input("Better WBW project ID: ").strip()
        if not project_id:
            print("❌ Geen project ID ingevoerd, stoppen.")
            return
    else:
        print(f"✓ Project gevonden: {PROJECT_STRUCTURE['name']}")

    print()

    # 3. Nieuwe milestone voor Bank Import v1
    milestone_name = "Bank Import v1 (Preview + Selectie)"
    milestone_description = (
        "MVP-flow voor bankimport: bestand inlezen, preview tonen, "
        "gebruiker laat kiezen welke posten worden ingeladen en pas daarna transacties maken."
    )

    milestone_id = create_milestone(project_id, milestone_name, milestone_description)
    if not milestone_id:
        print("❌ Kon milestone niet aanmaken.")
        return

    # 4. Tickets voor de preview/select/commit flow
    tickets: Dict[str, Dict] = {
        "TICKET-311": {
            "title": "Upload & preview sessies (backend)",
            "description": (
                "- Endpoint `POST /bank/import/preview` maken.\n"
                "- Bestand + type (`excel_txt`, later `camt053`/`mt940`) accepteren.\n"
                "- Bestand parsen via BankParser naar genormaliseerde rijen "
                "(`date`, `description`, `amount`, `balance`, ...).\n"
                "- Preview-rijen tijdelijk opslaan in een import_session (DB-tabel of in-memory) "
                "met `session_id`.\n"
                "- `session_id` + eerste ~50 rijen teruggeven aan de frontend (nog géén transacties maken)."
            ),
            "priority": "HIGH",
        },
        "TICKET-312": {
            "title": "Selecteer posten UI (frontend wizard)",
            "description": (
                "- Vue-wizard/modal bouwen voor bankimport.\n"
                "- Stap 1: bestand uploaden + type kiezen.\n"
                "- Stap 2: preview-tabel met checkbox per rij, 'selecteer alles / niets'.\n"
                "- State bewaren per rij (`selected: true/false`).\n"
                "- Op 'X posten importeren' wordt een lijst met geselecteerde row_ids naar de backend gestuurd."
            ),
            "priority": "MEDIUM",
        },
        "TICKET-313": {
            "title": "Commit geselecteerde posten als transacties",
            "description": (
                "- Endpoint `POST /bank/import/commit` maken.\n"
                "- Input: `session_id` + lijst `selected_row_ids`.\n"
                "- Gebruik de opgeslagen preview-rijen om alleen geselecteerde posten om te zetten naar "
                "`Transaction` + `TransactionSplit` records.\n"
                "- Alles binnen één DB-transaction uitvoeren.\n"
                "- JSON-respons met `imported_count`, `skipped_count` en optioneel lijst met duplicates."
            ),
            "priority": "HIGH",
        },
    }

    print("📋 Milestone en issues aanmaken in Linear...\n")
    for ticket in tickets.values():
        create_issue(team_id, project_id, milestone_id, ticket)

    print("\n✅ Bank Import tickets succesvol aangemaakt in Linear.")


if __name__ == "__main__":
    main()

