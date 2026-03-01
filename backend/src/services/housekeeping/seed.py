"""Built-in seed templates for housekeeping tasks."""

SEED_TEMPLATES = [
    {
        "name": "Security and Privacy Review",
        "title_pattern": "🔒 Security and Privacy Review – {date}",
        "body_content": (
            "## Security and Privacy Review\n\n"
            "Review the `#codebase` to ensure the highest level of security, "
            "privacy, and best practices.\n\n"
            "### Objectives\n\n"
            "- Audit authentication and authorization mechanisms\n"
            "- Review data handling and privacy compliance\n"
            "- Check for common vulnerabilities (OWASP Top 10)\n"
            "- Validate secrets management and environment configuration\n"
            "- Review dependency versions for known CVEs\n"
            "- Assess input validation and output encoding\n\n"
            "### Scope\n\n"
            "All source code, configuration files, and infrastructure definitions "
            "in the repository.\n\n"
            "### Expected Outputs\n\n"
            "- List of identified security concerns with severity ratings\n"
            "- Recommended fixes and mitigations\n"
            "- Updated dependency versions if needed\n"
        ),
        "category": "built-in",
    },
    {
        "name": "Test Coverage Refresh",
        "title_pattern": "🧪 Test Coverage Refresh – {date}",
        "body_content": (
            "## Test Coverage Refresh\n\n"
            "Increase quality testing and coverage across the `#codebase` "
            "using best practices while resolving bugs and issues.\n\n"
            "### Objectives\n\n"
            "- Identify untested or under-tested code paths\n"
            "- Add missing unit tests for critical business logic\n"
            "- Add integration tests for API endpoints\n"
            "- Improve edge case coverage\n"
            "- Fix flaky or failing tests\n"
            "- Update test fixtures and mocks as needed\n\n"
            "### Scope\n\n"
            "All source code and test files in the repository.\n\n"
            "### Expected Outputs\n\n"
            "- New test files or updated existing tests\n"
            "- Coverage report showing improvements\n"
            "- List of resolved test issues\n"
        ),
        "category": "built-in",
    },
    {
        "name": "Bug Bash",
        "title_pattern": "🐛 Bug Bash – {date}",
        "body_content": (
            "## Bug Bash\n\n"
            "Review the `#codebase` to find and resolve bugs and issues.\n\n"
            "### Objectives\n\n"
            "- Identify runtime errors, logic bugs, and edge cases\n"
            "- Review error handling and recovery paths\n"
            "- Check for resource leaks and performance issues\n"
            "- Validate data consistency and state management\n"
            "- Fix any identified issues with appropriate tests\n\n"
            "### Scope\n\n"
            "All source code in the repository with focus on recently "
            "changed areas.\n\n"
            "### Expected Outputs\n\n"
            "- List of identified bugs with reproduction steps\n"
            "- Bug fixes with corresponding tests\n"
            "- Documentation updates if behavior changes\n"
        ),
        "category": "built-in",
    },
]
