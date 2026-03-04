# Contracts: Add Green Background Color to App

**Feature**: 018-green-background | **Date**: 2026-03-04

## Overview

This feature has no API contracts. The change is a frontend-only CSS modification that does not introduce or modify any API endpoints, GraphQL schemas, WebSocket messages, or inter-service communication.

## Why No Contracts

- No backend changes required
- No new API endpoints
- No data exchange format changes
- The only "contract" is the CSS custom property interface between `index.css` and `tailwind.config.js`, which is documented in [data-model.md](../data-model.md)
