# Contracts: Update App Title to "Hello World"

**Feature**: 005-hello-world-title  
**Date**: 2026-02-19

## Overview

This feature does not introduce or modify any API endpoints. The only API-adjacent change is updating the FastAPI OpenAPI metadata (title and description), which affects the auto-generated Swagger UI documentation but does not change any request/response contracts.

## OpenAPI Metadata Changes

The following metadata fields in the FastAPI application configuration will be updated:

| Field | Current Value | New Value |
|-------|--------------|-----------|
| `title` | `"Agent Projects API"` | `"Hello World API"` |
| `description` | `"REST API for Agent Projects"` | `"REST API for Hello World"` |

These changes affect only the informational fields in the OpenAPI spec served at `/docs` and `/openapi.json`. No endpoint paths, request bodies, response schemas, or authentication flows are modified.

## No New Contracts

No new API contracts are introduced by this feature. All changes are cosmetic text replacements with no functional impact on the API surface.
