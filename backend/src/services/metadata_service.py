"""MetadataService — fetches, caches, and serves repository metadata for issue creation.

Provides labels, branches, milestones, and collaborators from the GitHub REST API,
persisted in SQLite with an in-memory L1 cache layer for performance.
"""

import json
import logging
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, Field

from src.config import get_settings
from src.constants import LABELS
from src.services.cache import InMemoryCache
from src.utils import utcnow

logger = logging.getLogger(__name__)


class RepositoryMetadataContext(BaseModel):
    """Cached repository metadata used for AI prompt injection and validation."""

    repo_key: str = Field(..., description="Repository identifier (owner/repo)")
    labels: list[dict] = Field(default_factory=list, description="Cached label objects")
    branches: list[dict] = Field(default_factory=list, description="Cached branch objects")
    milestones: list[dict] = Field(default_factory=list, description="Cached milestone objects")
    collaborators: list[dict] = Field(
        default_factory=list, description="Cached collaborator objects"
    )
    fetched_at: str = Field(default="", description="ISO 8601 timestamp of last fetch")
    is_stale: bool = Field(default=False, description="True if cache TTL has expired")
    source: str = Field(default="fresh", description="Data source: fresh, cache, or fallback")


class MetadataService:
    """Service for fetching and caching GitHub repository metadata.

    Implements a two-tier cache (L1 in-memory, L2 SQLite) with configurable
    TTL and three-tier fallback (API → SQLite → hardcoded constants).
    """

    def __init__(self, l1_cache: InMemoryCache | None = None) -> None:
        self._l1 = l1_cache or InMemoryCache()
        self._settings = get_settings()

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    async def get_or_fetch(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> RepositoryMetadataContext:
        """Return cached metadata if fresh, otherwise fetch from GitHub API.

        Three-tier fallback:
        1. L1 in-memory cache (fastest)
        2. L2 SQLite cache (survives restarts)
        3. Hardcoded constants from constants.py (last resort)
        """
        repo_key = f"{owner}/{repo}"
        ttl = self._settings.metadata_cache_ttl_seconds

        # Tier 1: L1 in-memory cache
        l1_data = self._l1.get(f"metadata:{repo_key}")
        if l1_data is not None:
            ctx = RepositoryMetadataContext(**l1_data)
            if not self._is_stale(ctx.fetched_at, ttl):
                ctx.is_stale = False
                ctx.source = "cache"
                return ctx

        # Tier 2: L2 SQLite cache
        try:
            ctx = await self._read_from_sqlite(repo_key)
            if ctx and not self._is_stale(ctx.fetched_at, ttl):
                ctx.source = "cache"
                ctx.is_stale = False
                # Populate L1
                self._l1.set(f"metadata:{repo_key}", ctx.model_dump(), ttl_seconds=ttl)
                return ctx
        except Exception:
            logger.warning("Failed to read metadata from SQLite for %s", repo_key, exc_info=True)

        # Tier 3: Fetch from API (with fallback on error)
        try:
            ctx = await self.fetch_metadata(access_token, owner, repo)
            return ctx
        except Exception:
            logger.warning(
                "Failed to fetch metadata from GitHub API for %s, falling back",
                repo_key,
                exc_info=True,
            )

        # Fallback: try stale SQLite data
        try:
            ctx = await self._read_from_sqlite(repo_key)
            if ctx:
                ctx.source = "cache"
                ctx.is_stale = True
                return ctx
        except Exception:
            pass

        # Last resort: hardcoded constants
        return self._fallback_context(repo_key)

    async def fetch_metadata(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> RepositoryMetadataContext:
        """Fetch metadata from GitHub REST API and persist in both caches."""
        repo_key = f"{owner}/{repo}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            labels = await self._fetch_paginated(
                client, f"https://api.github.com/repos/{owner}/{repo}/labels", headers
            )
            branches = await self._fetch_paginated(
                client, f"https://api.github.com/repos/{owner}/{repo}/branches", headers
            )
            milestones = await self._fetch_paginated(
                client,
                f"https://api.github.com/repos/{owner}/{repo}/milestones",
                headers,
                params={"state": "open"},
            )
            collaborators = await self._fetch_paginated(
                client, f"https://api.github.com/repos/{owner}/{repo}/collaborators", headers
            )

        now = utcnow().isoformat()
        ttl = self._settings.metadata_cache_ttl_seconds

        # Normalize to minimal dicts
        label_dicts = [
            {
                "name": lb.get("name", ""),
                "color": lb.get("color", ""),
                "description": lb.get("description", "") or "",
            }
            for lb in labels
        ]
        branch_dicts = [
            {"name": br.get("name", ""), "protected": br.get("protected", False)} for br in branches
        ]
        milestone_dicts = [
            {
                "number": ms.get("number", 0),
                "title": ms.get("title", ""),
                "due_on": ms.get("due_on"),
                "state": ms.get("state", "open"),
            }
            for ms in milestones
        ]
        collab_dicts = [
            {"login": co.get("login", ""), "avatar_url": co.get("avatar_url", "")}
            for co in collaborators
        ]

        ctx = RepositoryMetadataContext(
            repo_key=repo_key,
            labels=label_dicts,
            branches=branch_dicts,
            milestones=milestone_dicts,
            collaborators=collab_dicts,
            fetched_at=now,
            is_stale=False,
            source="fresh",
        )

        # Persist to L2 (SQLite) and L1 (memory)
        try:
            await self._write_to_sqlite(ctx)
        except Exception:
            logger.warning("Failed to write metadata to SQLite for %s", repo_key, exc_info=True)

        self._l1.set(f"metadata:{repo_key}", ctx.model_dump(), ttl_seconds=ttl)

        logger.info(
            "Fetched metadata for %s: %d labels, %d branches, %d milestones, %d collaborators",
            repo_key,
            len(label_dicts),
            len(branch_dicts),
            len(milestone_dicts),
            len(collab_dicts),
        )
        return ctx

    async def get_metadata(self, owner: str, repo: str) -> RepositoryMetadataContext | None:
        """Return cached metadata without fetching from API."""
        repo_key = f"{owner}/{repo}"
        ttl = self._settings.metadata_cache_ttl_seconds

        l1_data = self._l1.get(f"metadata:{repo_key}")
        if l1_data is not None:
            ctx = RepositoryMetadataContext(**l1_data)
            ctx.is_stale = self._is_stale(ctx.fetched_at, ttl)
            ctx.source = "cache"
            return ctx

        try:
            ctx = await self._read_from_sqlite(repo_key)
            if ctx:
                ctx.is_stale = self._is_stale(ctx.fetched_at, ttl)
                ctx.source = "cache"
                self._l1.set(f"metadata:{repo_key}", ctx.model_dump(), ttl_seconds=ttl)
                return ctx
        except Exception:
            logger.warning("Failed to read metadata from SQLite for %s", repo_key, exc_info=True)

        return None

    async def invalidate(self, owner: str, repo: str) -> None:
        """Clear cached metadata for a repository."""
        repo_key = f"{owner}/{repo}"
        self._l1.delete(f"metadata:{repo_key}")

        try:
            from src.services.database import get_db

            db = get_db()
            await db.execute(
                "DELETE FROM github_metadata_cache WHERE repo_key = ?",
                (repo_key,),
            )
            await db.commit()
            logger.info("Invalidated metadata cache for %s", repo_key)
        except Exception:
            logger.warning("Failed to invalidate SQLite cache for %s", repo_key, exc_info=True)

    # ──────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────

    async def _fetch_paginated(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict,
        params: dict | None = None,
    ) -> list[dict]:
        """Fetch all pages from a GitHub REST API list endpoint.

        Returns whatever results were fetched successfully. On API errors
        (rate limit, network, etc.) the loop breaks and partial results
        are returned — the caller handles the fallback logic.
        """
        results: list[dict] = []
        page = 1
        per_page = 100
        base_params = dict(params or {})

        while True:
            request_params = {**base_params, "per_page": per_page, "page": page}
            try:
                response = await client.get(url, headers=headers, params=request_params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (403, 429):
                    logger.warning(
                        "GitHub API rate limit or forbidden for %s: %s",
                        url,
                        exc.response.status_code,
                    )
                elif exc.response.status_code == 404:
                    logger.debug("GitHub API 404 for %s (resource may not exist)", url)
                else:
                    logger.warning("GitHub API error for %s: %s", url, exc.response.status_code)
                break
            except httpx.ConnectError:
                logger.warning("Network error fetching %s", url)
                break

            data = response.json()
            if not isinstance(data, list) or not data:
                break

            results.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return results

    async def _read_from_sqlite(self, repo_key: str) -> RepositoryMetadataContext | None:
        """Read cached metadata from SQLite."""
        from src.services.database import get_db

        db = get_db()

        rows = await db.execute_fetchall(
            "SELECT field_type, value, fetched_at FROM github_metadata_cache WHERE repo_key = ?",
            (repo_key,),
        )
        if not rows:
            return None

        labels: list[dict] = []
        branches: list[dict] = []
        milestones: list[dict] = []
        collaborators: list[dict] = []
        fetched_at = ""

        for row in rows:
            field_type = row[0]  # type: ignore[index]
            value_json = row[1]  # type: ignore[index]
            row_fetched = row[2]  # type: ignore[index]
            if not fetched_at or row_fetched > fetched_at:
                fetched_at = row_fetched

            try:
                value = json.loads(value_json)
            except json.JSONDecodeError:
                continue

            if field_type == "label":
                labels.append(value)
            elif field_type == "branch":
                branches.append(value)
            elif field_type == "milestone":
                milestones.append(value)
            elif field_type == "collaborator":
                collaborators.append(value)

        return RepositoryMetadataContext(
            repo_key=repo_key,
            labels=labels,
            branches=branches,
            milestones=milestones,
            collaborators=collaborators,
            fetched_at=fetched_at,
            is_stale=False,
            source="cache",
        )

    async def _write_to_sqlite(self, ctx: RepositoryMetadataContext) -> None:
        """Write metadata to SQLite, replacing existing entries."""
        from src.services.database import get_db

        db = get_db()

        # Delete existing entries for this repo
        await db.execute(
            "DELETE FROM github_metadata_cache WHERE repo_key = ?",
            (ctx.repo_key,),
        )

        # Insert new entries
        rows: list[tuple[str, str, str, str]] = []
        for label in ctx.labels:
            rows.append((ctx.repo_key, "label", json.dumps(label), ctx.fetched_at))
        for branch in ctx.branches:
            rows.append((ctx.repo_key, "branch", json.dumps(branch), ctx.fetched_at))
        for milestone in ctx.milestones:
            rows.append((ctx.repo_key, "milestone", json.dumps(milestone), ctx.fetched_at))
        for collab in ctx.collaborators:
            rows.append((ctx.repo_key, "collaborator", json.dumps(collab), ctx.fetched_at))

        if rows:
            await db.executemany(
                "INSERT OR REPLACE INTO github_metadata_cache (repo_key, field_type, value, fetched_at) "
                "VALUES (?, ?, ?, ?)",
                rows,
            )
            await db.commit()

    def _is_stale(self, fetched_at: str, ttl_seconds: int) -> bool:
        """Check if a fetched_at timestamp is older than TTL."""
        if not fetched_at:
            return True
        try:
            fetched = datetime.fromisoformat(fetched_at)
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=UTC)
            now = utcnow()
            return (now - fetched).total_seconds() > ttl_seconds
        except (ValueError, TypeError):
            return True

    def _fallback_context(self, repo_key: str) -> RepositoryMetadataContext:
        """Return a fallback context using hardcoded constants."""
        return RepositoryMetadataContext(
            repo_key=repo_key,
            labels=[{"name": lb, "color": "", "description": ""} for lb in LABELS],
            branches=[{"name": "main", "protected": True}],
            milestones=[],
            collaborators=[],
            fetched_at=utcnow().isoformat(),
            is_stale=False,
            source="fallback",
        )
