# Contracts: Startup Config Validation

This feature does not introduce any new API endpoints, GraphQL schemas, or external contracts.

All validation is internal to the `Settings` model validator and produces `ValueError` exceptions or `logging.warning()` calls. No API surface changes are needed.
