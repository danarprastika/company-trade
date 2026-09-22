"""
G1.12 — Migration Framework

Versioned, tested, and recoverable database migration system.
Never silently rewrite historical trading evidence.

Specification references:
- docs/13_implementation/04_MIGRATION_POLICY.md:
  "Never silently rewrite historical trading evidence."
  "Introduce compatibility layer → migrate → validate → remove old path only after evidence."
- docs/02_architecture/06_DATABASE_ARCHITECTURE.md:
  "Schema changes are versioned, tested and recoverable."
- docs/00_governance/05_CHANGE_MANAGEMENT.md:
  "Live-impacting changes require impact analysis, tests, approval, deployment evidence and rollback plan."
- docs/13_implementation/01_IMPLEMENTATION_RULES.md:
  "No governance bypass."
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .errors import PersistenceError
from .time import Instant


@dataclass(frozen=True)
class Migration:
    """
    A single database migration.
    Per MIGRATION_POLICY.md: "Introduce compatibility layer → migrate → validate → remove old path only after evidence."
    """

    version: str
    name: str
    description: str
    up_sql: str
    down_sql: str
    checksum: str = field(init=False)

    def __post_init__(self) -> None:
        # Compute checksum from migration content
        content = f"{self.version}:{self.name}:{self.up_sql}:{self.down_sql}"
        object.__setattr__(
            self, "checksum", hashlib.sha256(content.encode("utf-8")).hexdigest()
        )

    def verify_checksum(self) -> bool:
        """Verify that the migration content matches its checksum."""
        content = f"{self.version}:{self.name}:{self.up_sql}:{self.down_sql}"
        computed = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return computed == self.checksum


@dataclass(frozen=True)
class MigrationRecord:
    """
    Record of an applied migration.
    """

    version: str
    name: str
    applied_at: Instant
    applied_by: str
    checksum: str
    execution_time_ms: int


class MigrationStore(ABC):
    """
    Abstract store for migration records.
    """

    @abstractmethod
    def record_applied(self, record: MigrationRecord) -> None:
        """Record that a migration was applied."""
        pass

    @abstractmethod
    def get_applied_migrations(self) -> List[MigrationRecord]:
        """Get all applied migrations, ordered by version."""
        pass

    @abstractmethod
    def get_last_applied_version(self) -> Optional[str]:
        """Get the version of the last applied migration."""
        pass

    @abstractmethod
    def remove_record(self, version: str) -> None:
        """Remove a migration record (for rollback)."""
        pass


class MigrationExecutor(ABC):
    """
    Abstract executor for running migration SQL.
    """

    @abstractmethod
    def execute(self, sql: str) -> None:
        """Execute a SQL statement."""
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass

    @abstractmethod
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass


class MigrationManager:
    """
    Manages database migrations with versioning, validation, and rollback.
    Per MIGRATION_POLICY.md: "Schema changes are versioned, tested and recoverable."
    Per DATABASE_ARCHITECTURE.md: "Never silently rewrite historical trading evidence."
    """

    def __init__(
        self,
        migrations: List[Migration],
        store: MigrationStore,
        executor: MigrationExecutor,
    ) -> None:
        self._migrations = {m.version: m for m in sorted(migrations, key=lambda m: m.version)}
        self._store = store
        self._executor = executor
        self._applied: List[MigrationRecord] = []

    def _load_applied(self) -> None:
        """Load applied migrations from the store."""
        self._applied = self._store.get_applied_migrations()

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that have not been applied yet."""
        self._load_applied()
        applied_versions = {r.version for r in self._applied}
        return [
            m for m in self._migrations.values()
            if m.version not in applied_versions
        ]

    def get_applied_migrations(self) -> List[MigrationRecord]:
        """Get all applied migrations."""
        self._load_applied()
        return list(self._applied)

    def get_current_version(self) -> Optional[str]:
        """Get the current migration version."""
        self._load_applied()
        if not self._applied:
            return None
        return self._applied[-1].version

    def validate(self) -> List[str]:
        """
        Validate migration integrity.
        Returns list of validation errors (empty if valid).
        """
        errors: List[str] = []

        # Check for duplicate versions
        versions = [m.version for m in self._migrations.values()]
        if len(versions) != len(set(versions)):
            errors.append("Duplicate migration versions found")

        # Check checksums of applied migrations
        self._load_applied()
        for record in self._applied:
            migration = self._migrations.get(record.version)
            if migration is None:
                errors.append(f"Applied migration {record.version} not found in migration set")
            elif migration.checksum != record.checksum:
                errors.append(
                    f"Checksum mismatch for migration {record.version}: "
                    f"expected {record.checksum}, got {migration.checksum}"
                )

        return errors

    def up(self, target_version: Optional[str] = None) -> List[MigrationRecord]:
        """
        Apply pending migrations up to target_version (or all if None).
        Per MIGRATION_POLICY.md: "Introduce compatibility layer → migrate → validate → remove old path only after evidence."
        """
        self._load_applied()
        applied: List[MigrationRecord] = []

        pending = self.get_pending_migrations()
        if target_version:
            pending = [m for m in pending if m.version <= target_version]

        for migration in pending:
            # Verify checksum before applying
            if not migration.verify_checksum():
                raise PersistenceError(
                    message=f"Migration {migration.version} checksum verification failed",
                )

            self._executor.begin_transaction()
            try:
                self._executor.execute(migration.up_sql)
                record = MigrationRecord(
                    version=migration.version,
                    name=migration.name,
                    applied_at=Instant.now(),
                    applied_by="migration_manager",
                    checksum=migration.checksum,
                    execution_time_ms=0,  # Would be measured in real implementation
                )
                self._store.record_applied(record)
                self._executor.commit_transaction()
                applied.append(record)
            except Exception as e:
                self._executor.rollback_transaction()
                raise PersistenceError(
                    message=f"Migration {migration.version} failed: {str(e)}",
                ) from e

        return applied

    def down(self, target_version: str) -> List[MigrationRecord]:
        """
        Rollback migrations down to target_version.
        Per MIGRATION_POLICY.md: "remove old path only after evidence."
        """
        self._load_applied()
        rolled_back: List[MigrationRecord] = []

        # Get migrations to rollback (in reverse order)
        to_rollback = [
            r for r in reversed(self._applied)
            if r.version > target_version
        ]

        for record in to_rollback:
            migration = self._migrations.get(record.version)
            if migration is None:
                raise PersistenceError(
                    message=f"Cannot rollback: migration {record.version} not found",
                )

            self._executor.begin_transaction()
            try:
                self._executor.execute(migration.down_sql)
                self._store.remove_record(record.version)
                self._executor.commit_transaction()
                rolled_back.append(record)
            except Exception as e:
                self._executor.rollback_transaction()
                raise PersistenceError(
                    message=f"Rollback of migration {record.version} failed: {str(e)}",
                ) from e

        return rolled_back

    def info(self) -> Dict[str, Any]:
        """Get migration status information."""
        self._load_applied()
        applied_versions = {r.version for r in self._applied}

        return {
            "current_version": self.get_current_version(),
            "total_migrations": len(self._migrations),
            "applied_count": len(self._applied),
            "pending_count": len(self.get_pending_migrations()),
            "migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "applied": m.version in applied_versions,
                    "checksum": m.checksum,
                }
                for m in self._migrations.values()
            ],
        }


class InMemoryMigrationStore(MigrationStore):
    """
    In-memory migration store for G1 foundation.
    """

    def __init__(self) -> None:
        self._records: List[MigrationRecord] = []

    def record_applied(self, record: MigrationRecord) -> None:
        self._records.append(record)

    def get_applied_migrations(self) -> List[MigrationRecord]:
        return sorted(self._records, key=lambda r: r.version)

    def get_last_applied_version(self) -> Optional[str]:
        if not self._records:
            return None
        return max(r.version for r in self._records)

    def remove_record(self, version: str) -> None:
        self._records = [r for r in self._records if r.version != version]


class InMemoryMigrationExecutor(MigrationExecutor):
    """
    In-memory migration executor for G1 foundation.
    Records executed SQL for validation.
    """

    def __init__(self) -> None:
        self._executed: List[str] = []
        self._in_transaction: bool = False

    def execute(self, sql: str) -> None:
        self._executed.append(sql)

    def begin_transaction(self) -> None:
        self._in_transaction = True

    def commit_transaction(self) -> None:
        self._in_transaction = False

    def rollback_transaction(self) -> None:
        self._in_transaction = False
        # Remove last executed statement (simplified)
        if self._executed:
            self._executed.pop()

    @property
    def executed(self) -> List[str]:
        return list(self._executed)


__all__ = [
    "Migration",
    "MigrationRecord",
    "MigrationStore",
    "MigrationExecutor",
    "MigrationManager",
    "InMemoryMigrationStore",
    "InMemoryMigrationExecutor",
]
