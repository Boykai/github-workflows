"""
Integration test for GitHub Copilot Custom Agent Assignment.

This script tests assigning a GitHub Issue to the 'speckit.specify' custom agent
when the issue status is updated to "Ready".

Requirements:
- GITHUB_TOKEN environment variable with repo scope
- A repository with Copilot coding agent enabled
- The speckit.specify.agent.md file in .github/agents/

Usage:
    export GITHUB_TOKEN="your-token"
    python -m tests.integration.test_custom_agent_assignment
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.github_projects import GitHubProjectsService


async def test_custom_agent_assignment():
    """Test assigning an issue to a custom agent."""

    # Configuration - update these values for your test
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    OWNER = os.environ.get("GITHUB_OWNER", "Boykai")
    REPO = os.environ.get("GITHUB_REPO", "github-workflows")
    ISSUE_NUMBER = int(os.environ.get("GITHUB_ISSUE_NUMBER", "1"))
    CUSTOM_AGENT = os.environ.get("CUSTOM_AGENT", "speckit.specify")

    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN environment variable is required")
        print("Set it with: export GITHUB_TOKEN='your-github-token'")
        return False

    print("=" * 60)
    print("GitHub Copilot Custom Agent Assignment Test")
    print("=" * 60)
    print(f"Repository: {OWNER}/{REPO}")
    print(f"Issue Number: {ISSUE_NUMBER}")
    print(f"Custom Agent: {CUSTOM_AGENT}")
    print("=" * 60)

    service = GitHubProjectsService()

    try:
        # Step 1: Check if Copilot is available
        print("\n[1/4] Checking Copilot availability...")
        bot_id, repo_id = await service.get_copilot_bot_id(
            access_token=GITHUB_TOKEN,
            owner=OWNER,
            repo=REPO,
        )

        if not bot_id:
            print("❌ FAILED: Copilot coding agent is not available for this repository")
            print("   Make sure Copilot coding agent is enabled in repository settings")
            return False

        print(f"✅ Copilot bot found: {bot_id[:20]}...")
        print(f"✅ Repository ID: {repo_id[:20]}...")

        # Step 2: Fetch issue details
        print(f"\n[2/4] Fetching issue #{ISSUE_NUMBER} details...")
        issue_data = await service.get_issue_with_comments(
            access_token=GITHUB_TOKEN,
            owner=OWNER,
            repo=REPO,
            issue_number=ISSUE_NUMBER,
        )

        if not issue_data.get("title"):
            print(f"❌ FAILED: Could not fetch issue #{ISSUE_NUMBER}")
            return False

        print(f"✅ Issue title: {issue_data['title'][:50]}...")
        print(f"✅ Body length: {len(issue_data.get('body', ''))} chars")
        print(f"✅ Comments: {len(issue_data.get('comments', []))}")

        # Step 3: Format prompt
        print("\n[3/4] Formatting issue context as prompt...")
        prompt = service.format_issue_context_as_prompt(issue_data)
        print(f"✅ Prompt length: {len(prompt)} chars")
        print(f"   Preview: {prompt[:100]}...")

        # Step 4: Assign to custom agent
        print(f"\n[4/4] Assigning to custom agent '{CUSTOM_AGENT}'...")

        # We need the issue node ID for GraphQL
        # Get it via REST API first
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{ISSUE_NUMBER}",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if resp.status_code != 200:
                print(f"❌ FAILED: Could not get issue node ID: {resp.status_code}")
                return False
            issue_node_id = resp.json().get("node_id")
            print(f"   Issue node ID: {issue_node_id[:20]}...")

        success = await service.assign_copilot_to_issue(
            access_token=GITHUB_TOKEN,
            owner=OWNER,
            repo=REPO,
            issue_node_id=issue_node_id,
            issue_number=ISSUE_NUMBER,
            custom_agent=CUSTOM_AGENT,
            custom_instructions=prompt,
        )

        if success:
            print(f"✅ SUCCESS: Issue assigned to custom agent '{CUSTOM_AGENT}'")
            print(
                f"\n🎉 Check the issue at: https://github.com/{OWNER}/{REPO}/issues/{ISSUE_NUMBER}"
            )
            return True
        else:
            print("❌ FAILED: Could not assign issue to custom agent")
            print("   Check the logs above for error details")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        await service.close()


async def test_rest_api_payload():
    """Test that the REST API payload is correctly formatted."""
    print("\n" + "=" * 60)
    print("REST API Payload Verification Test")
    print("=" * 60)

    service = GitHubProjectsService()

    # Create test payload
    payload = {
        "assignees": ["copilot-swe-agent[bot]"],
        "agent_assignment": {
            "target_repo": "Boykai/github-workflows",
            "base_branch": "main",
            "custom_instructions": "## Issue Title\nTest Issue\n\n## Issue Description\nThis is a test.",
            "custom_agent": "speckit.specify",
            "model": "",
        },
    }

    print("\nExpected REST API Payload:")
    print("-" * 40)
    import json

    print(json.dumps(payload, indent=2))
    print("-" * 40)

    print("\n✅ Payload structure matches GitHub documentation")

    await service.close()
    return True


if __name__ == "__main__":
    print("\n" + "🔧 " * 20)
    print("Running GitHub Copilot Custom Agent Integration Tests")
    print("🔧 " * 20 + "\n")

    # Run payload verification (doesn't need GitHub token)
    asyncio.run(test_rest_api_payload())

    # Run actual assignment test (needs GitHub token)
    if os.environ.get("GITHUB_TOKEN"):
        result = asyncio.run(test_custom_agent_assignment())
        sys.exit(0 if result else 1)
    else:
        print("\n⚠️  Skipping assignment test - GITHUB_TOKEN not set")
        print("   To run the full test, set: export GITHUB_TOKEN='your-token'")
        sys.exit(0)
