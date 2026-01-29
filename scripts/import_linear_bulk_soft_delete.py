#!/usr/bin/env python3
"""
Linear Import - Bulk transacties & soft delete

Maakt één milestone en één issue aan in het bestaande Better WBW project
met de volledige changelog (CHANGELOG_BULK_SOFT_DELETE.md) + commit log.
Gebruik het issue in Linear om uit te besteden en als referentie voor commit.

Usage:
    python scripts/import_linear_bulk_soft_delete.py

Requirements:
    - LINEAR_API_KEY en optioneel LINEAR_TEAM_ID in .env
"""

import sys
from pathlib import Path

# Allow importing from scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_linear import (
    LINEAR_API_KEY,
    PROJECT_STRUCTURE,
    linear_query,
    get_team_id,
    create_milestone,
    create_issue,
)


def get_project_id(team_id: str):
    """Zoek het bestaande 'Better WBW' project op basis van naam."""
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
        if "errors" in result:
            return None
        projects = result.get("data", {}).get("projects", {}).get("nodes", [])
        for p in projects:
            if p.get("name") == PROJECT_STRUCTURE["name"]:
                team_ids = [t.get("id") for t in p.get("teams", {}).get("nodes", [])]
                if team_id in team_ids:
                    return p.get("id")
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
        result = linear_query(query_fallback, {"teamId": team_id})
        if "errors" in result:
            return None
        projects = (
            result.get("data", {}).get("team", {}).get("projects", {}).get("nodes", [])
        )
        for p in projects:
            if p.get("name") == PROJECT_STRUCTURE["name"]:
                return p.get("id")
        return None
    except Exception:
        return None


def main():
    print("🚀 Linear Import - Bulk transacties & soft delete\n")

    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY niet gevonden in .env")
        print("   Zet LINEAR_API_KEY=... in je .env bestand.")
        sys.exit(1)

    team_id = get_team_id()
    print("\n🔍 Zoeken naar project: Better WBW...")
    project_id = get_project_id(team_id)

    if not project_id:
        print("\n⚠️  Project niet automatisch gevonden.")
        print(
            "Plak de project ID (UUID) van je bestaande 'Better WBW' project hier.\n"
            "Tip: open het project in Linear, Cmd/Ctrl+K → 'Copy model UUID'."
        )
        project_id = input("Better WBW project ID: ").strip()
        if not project_id:
            print("❌ Geen project ID ingevoerd.")
            sys.exit(1)
    else:
        print(f"✓ Project gevonden: {PROJECT_STRUCTURE['name']}")

    # Milestone
    milestone_name = "Bulk transacties & soft delete"
    milestone_description = (
        "Eenvoudig meerdere transacties koppelen aan een activiteit of "
        "dezelfde personen toepassen; verwijderen eerst soft (prullenbak), daarna optioneel hard."
    )
    milestone_id = create_milestone(project_id, milestone_name, milestone_description)
    if not milestone_id:
        print("❌ Kon milestone niet aanmaken.")
        sys.exit(1)

    # Issue: volledige changelog + commit log (voor uitbesteden en als commit-referentie)
    root = Path(__file__).resolve().parent.parent
    changelog_doc = root / "CHANGELOG_BULK_SOFT_DELETE.md"
    commit_log_doc = root / "COMMIT_LOG.md"

    description = ""
    if changelog_doc.exists():
        description = changelog_doc.read_text(encoding="utf-8")
        description += "\n\n---\n\n## Commit log (gebruik bij committen)\n\n"
    else:
        description = "Zie CHANGELOG_BULK_SOFT_DELETE.md in de repo voor het volledige overzicht.\n\n---\n\n## Commit log\n\n"

    if commit_log_doc.exists():
        description += commit_log_doc.read_text(encoding="utf-8")
    else:
        description += "```\nfeat: bulk transacties, soft delete en prullenbak\n- Backend: deleted_at, soft/restore/permanent, PATCH /transactions/bulk\n- Frontend: prullenbak-tab, bulk selectie + modals\n```\n"

    ticket = {
        "title": "Bulk transacties & soft delete – changelog, uitbesteden & commit log",
        "description": description,
        "priority": "MEDIUM",
    }

    print("\n📋 Issue aanmaken in Linear (volledige changelog + commit log)...\n")
    create_issue(team_id, project_id, milestone_id, ticket)
    print("\n✅ Klaar. Check je Linear project voor de nieuwe milestone en issue.")
    print("   Gebruik het issue om uit te besteden en als referentie voor de commit.")
    if changelog_doc.exists():
        print(f"   (Changelog: {changelog_doc.name})")
    if commit_log_doc.exists():
        print(f"   (Commit log: {commit_log_doc.name})")


if __name__ == "__main__":
    main()
