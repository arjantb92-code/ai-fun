#!/usr/bin/env python3
"""
Linear Import Script - Better WBW Project
Imports milestones and issues into Linear from a structured definition.

Usage:
    python scripts/import_linear.py

Requirements:
    - Linear API key in .env as LINEAR_API_KEY
    - Linear Team ID in .env as LINEAR_TEAM_ID (or will prompt)
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")

LINEAR_API_URL = "https://api.linear.app/graphql"

# Project structure definition
PROJECT_STRUCTURE = {
    "name": "Better WBW",
    "description": "Een high-end, zero-sum groepsuitgaven tracker met AI-bonnetjesscan en bank-import.",
    "milestones": [
        {
            "name": "Core Foundation & Auth (MVP)",
            "description": "Een stabiele, beveiligde basis waarop we verder kunnen bouwen.",
            "tickets": [
                {
                    "id": "TICKET-101",
                    "title": "Database Schema & Setup",
                    "description": """- Setup PostgreSQL in Docker.
- Implementeer User, Transaction, Split en Settlement modellen in Flask.
- Zet Flask-Migrate op voor schema-wijzigingen.""",
                    "priority": "HIGH"
                },
                {
                    "id": "TICKET-102",
                    "title": "JWT Authenticatie Systeem",
                    "description": """- Implementeer /login endpoint met password hashing (PBKDF2).
- Bouw @token_required decorator voor backend routes.
- Maak "Restricted Access" scherm in Frontend dat automatisch triggert zonder token.""",
                    "priority": "HIGH"
                },
                {
                    "id": "TICKET-103",
                    "title": "Gebruikersprofielen",
                    "description": """- Voeg velden toe voor Avatar en Email.
- Bouw "Edit Profile" modal in frontend.
- Implementeer beveiligde file-upload voor profielfoto's.""",
                    "priority": "MEDIUM"
                }
            ]
        },
        {
            "name": "Transactie Beheer & Balans",
            "description": "De kernfunctionaliteit van het verrekenen werkend krijgen.",
            "tickets": [
                {
                    "id": "TICKET-201",
                    "title": "Transactie CRUD",
                    "description": """- Bouw endpoints voor Create, Read, Update, Delete van transacties.
- Frontend: Lijstweergave met datum-groepering ("Vandaag", "Gisteren").
- Implementeer tabs voor "Uitgave", "Inkomsten" en "Transfer".""",
                    "priority": "HIGH"
                },
                {
                    "id": "TICKET-202",
                    "title": "Zero-Sum Balans Logica",
                    "description": """- Implementeer algoritme dat realtime balansen berekent.
- Zorg dat som van alle balansen altijd 0 is.
- Visuele weergave in frontend: Rood voor schuld, Wit voor tegoed.""",
                    "priority": "HIGH"
                },
                {
                    "id": "TICKET-203",
                    "title": "Settlement Engine",
                    "description": """- Bouw algoritme dat "Wie betaalt wie" optimaliseert (minste aantal transacties).
- Maak "Afrekening maken" knop die huidige stand archiveert naar historie.""",
                    "priority": "HIGH"
                }
            ]
        },
        {
            "name": "Import & AI Integraties",
            "description": "Het invoeren van data zo frictieloos mogelijk maken.",
            "tickets": [
                {
                    "id": "TICKET-301",
                    "title": "Bank Import Module",
                    "description": """- Schrijf parsers voor ING en ABN AMRO CSV-formaten.
- Bouw frontend import-modal met preview & selectie stap.""",
                    "priority": "MEDIUM"
                },
                {
                    "id": "TICKET-302",
                    "title": "OCR Bonnetjes Scanner",
                    "description": """- Integreer EasyOCR (of Tesseract) in backend.
- Bouw /ocr/process endpoint dat bedrag en datum extraheert.
- Drag-and-drop zone maken in transactie-modal.""",
                    "priority": "MEDIUM"
                }
            ]
        },
        {
            "name": "UI Polish & Hosting (TrainMore Style)",
            "description": "Een slick, professioneel product neerzetten.",
            "tickets": [
                {
                    "id": "TICKET-401",
                    "title": "TrainMore Design System",
                    "description": """- Implementeer Tailwind config met Brand Red (#E30613), Zwart en Industrial fonts (Oswald).
- Voeg micro-interacties toe (hover states, active scales).
- Zorg voor "Tactile" feedback op alle knoppen.""",
                    "priority": "MEDIUM"
                },
                {
                    "id": "TICKET-402",
                    "title": "Docker Productie Setup",
                    "description": """- Maak Dockerfile voor frontend (build step) en backend.
- Schrijf docker-compose.prod.yml voor server-deployment.
- Configureer Nginx als reverse proxy.""",
                    "priority": "LOW"
                }
            ]
        },
        {
            "name": "Backlog / Nice-to-haves",
            "description": "Future enhancements",
            "tickets": [
                {
                    "id": "TICKET-501",
                    "title": "iDEAL / Tikkie betaallink generatie bij settlements",
                    "description": "Integreer betaallink generatie voor settlements.",
                    "priority": "LOW"
                },
                {
                    "id": "TICKET-502",
                    "title": "Push notificaties bij nieuwe uitgaven",
                    "description": "Implementeer push notifications voor nieuwe transacties.",
                    "priority": "LOW"
                },
                {
                    "id": "TICKET-503",
                    "title": "Mobiele PWA (Progressive Web App) manifest",
                    "description": "Maak de app installable als PWA op mobiele devices.",
                    "priority": "LOW"
                }
            ]
        }
    ]
}


def linear_query(query: str, variables: Optional[Dict] = None) -> Dict:
    """Execute a GraphQL query against Linear API."""
    headers = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(LINEAR_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def get_team_id() -> str:
    """Get or prompt for Linear Team ID."""
    if LINEAR_TEAM_ID:
        return LINEAR_TEAM_ID
    
    # Try to fetch teams
    query = """
    query {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    
    try:
        result = linear_query(query)
        teams = result.get("data", {}).get("teams", {}).get("nodes", [])
        
        if not teams:
            print("❌ No teams found. Please create a team in Linear first.")
            sys.exit(1)
        
        print("\n📋 Available Teams:")
        for i, team in enumerate(teams, 1):
            print(f"  {i}. {team['name']} (Key: {team['key']})")
        
        choice = input("\nSelect team number: ").strip()
        try:
            selected = teams[int(choice) - 1]
            print(f"✓ Using team: {selected['name']} ({selected['id']})")
            return selected['id']
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error fetching teams: {e}")
        print("\n💡 You can also set LINEAR_TEAM_ID in .env")
        sys.exit(1)


def create_project(team_id: str) -> Optional[str]:
    """Create a project in Linear."""
    query = """
    mutation CreateProject($input: ProjectCreateInput!) {
      projectCreate(input: $input) {
        success
        project {
          id
          name
        }
      }
    }
    """
    
    variables = {
        "input": {
            "name": PROJECT_STRUCTURE["name"],
            "description": PROJECT_STRUCTURE["description"],
            "teamIds": [team_id]
        }
    }
    
    try:
        result = linear_query(query, variables)
        if result.get("data", {}).get("projectCreate", {}).get("success"):
            project_id = result["data"]["projectCreate"]["project"]["id"]
            print(f"✓ Created project: {PROJECT_STRUCTURE['name']}")
            return project_id
        else:
            print("⚠️  Project creation returned success=false")
            return None
    except Exception as e:
        print(f"⚠️  Error creating project (may already exist): {e}")
        return None


def create_milestone(project_id: str, name: str, description: str) -> Optional[str]:
    """Create a milestone in Linear."""
    query = """
    mutation CreateProjectMilestone($input: ProjectMilestoneCreateInput!) {
      projectMilestoneCreate(input: $input) {
        success
        projectMilestone {
          id
          name
        }
      }
    }
    """
    
    variables = {
        "input": {
            "name": name,
            "description": description,
            "projectId": project_id
        }
    }
    
    try:
        result = linear_query(query, variables)
        if result.get("data", {}).get("projectMilestoneCreate", {}).get("success"):
            milestone_id = result["data"]["projectMilestoneCreate"]["projectMilestone"]["id"]
            print(f"  ✓ Milestone: {name}")
            return milestone_id
        else:
            print(f"  ⚠️  Milestone creation failed for: {name}")
            return None
    except Exception as e:
        print(f"  ⚠️  Error creating milestone '{name}': {e}")
        return None


def priority_to_linear(priority: str) -> int:
    """Convert priority string to Linear priority number."""
    mapping = {
        "URGENT": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4
    }
    return mapping.get(priority.upper(), 3)


def create_issue(team_id: str, project_id: str, milestone_id: Optional[str], 
                 ticket: Dict) -> Optional[str]:
    """Create an issue in Linear."""
    query = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
        }
      }
    }
    """
    
    variables = {
        "input": {
            "teamId": team_id,
            "title": ticket["title"],
            "description": ticket["description"],
            "priority": priority_to_linear(ticket.get("priority", "MEDIUM")),
            "projectId": project_id
        }
    }
    
    if milestone_id:
        variables["input"]["projectMilestoneId"] = milestone_id
    
    try:
        result = linear_query(query, variables)
        if result.get("data", {}).get("issueCreate", {}).get("success"):
            issue = result["data"]["issueCreate"]["issue"]
            print(f"    ✓ {issue['identifier']}: {ticket['title']}")
            return issue["id"]
        else:
            print(f"    ⚠️  Issue creation failed: {ticket['title']}")
            return None
    except Exception as e:
        print(f"    ⚠️  Error creating issue '{ticket['title']}': {e}")
        return None


def main():
    """Main import function."""
    print("🚀 Linear Import Script - Better WBW\n")
    
    # Check API key
    if not LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY not found in .env")
        print("\n💡 Get your API key from: https://linear.app/settings/api")
        print("   Add to .env: LINEAR_API_KEY=your_key_here")
        sys.exit(1)
    
    # Get team ID
    team_id = get_team_id()
    
    # Create project
    print(f"\n📦 Creating project: {PROJECT_STRUCTURE['name']}")
    project_id = create_project(team_id)
    
    if not project_id:
        print("⚠️  Could not create project. Continuing with milestones/issues...")
        # Try to find existing project
        query = """
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
            result = linear_query(query, {"teamId": team_id})
            projects = result.get("data", {}).get("team", {}).get("projects", {}).get("nodes", [])
            matching = [p for p in projects if p["name"] == PROJECT_STRUCTURE["name"]]
            if matching:
                project_id = matching[0]["id"]
                print(f"✓ Using existing project: {PROJECT_STRUCTURE['name']}")
            else:
                print("❌ No project found. Please create it manually in Linear.")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error finding project: {e}")
            sys.exit(1)
    
    # Create milestones and issues
    print(f"\n📋 Creating milestones and issues...\n")
    
    for milestone_data in PROJECT_STRUCTURE["milestones"]:
        milestone_id = create_milestone(
            project_id,
            milestone_data["name"],
            milestone_data["description"]
        )
        
        for ticket in milestone_data["tickets"]:
            create_issue(team_id, project_id, milestone_id, ticket)
    
    print(f"\n✅ Import complete!")
    print(f"\n📝 Next steps:")
    print(f"   1. Check your Linear workspace for the '{PROJECT_STRUCTURE['name']}' project")
    print(f"   2. Review and adjust priorities/assignees as needed")
    print(f"   3. Start working on tickets!")


if __name__ == "__main__":
    main()
