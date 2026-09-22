"""
G1.12 — Unit tests for Migration Framework

Tests:
- Migration creation and checksum
- Migration manager up/down
- Migration validation
- Migration info
- Rollback capability
"""

import pytest
from src.domain.migration import (
    Migration,
    MigrationRecord,
    MigrationManager,
    InMemoryMigrationStore,
    InMemoryMigrationExecutor,
)
from src.domain.errors import PersistenceError
from src.domain.time import Instant


class TestMigration:
    def test_creation(self):
        """Migration should be created with all fields."""
        m = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="DROP TABLE test;",
        )
        assert m.version == "001"
        assert m.name == "initial_schema"
        assert m.checksum is not None
        assert len(m.checksum) == 64

    def test_checksum_deterministic(self):
        """Same migration content should produce same checksum."""
        m1 = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="DROP TABLE test;",
        )
        m2 = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="DROP TABLE test;",
        )
        assert m1.checksum == m2.checksum

    def test_checksum_different_content(self):
        """Different migration content should produce different checksum."""
        m1 = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="DROP TABLE test;",
        )
        m2 = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE test (id INTEGER);",
            down_sql="DROP TABLE test;",
        )
        assert m1.checksum != m2.checksum

    def test_verify_checksum(self):
        """verify_checksum should return True for valid checksum."""
        m = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE test (id TEXT);",
            down_sql="DROP TABLE test;",
        )
        assert m.verify_checksum() is True


class TestMigrationManager:
    def _make_migrations(self) -> list:
        return [
            Migration(
                version="001",
                name="initial_schema",
                description="Initial schema",
                up_sql="CREATE TABLE test (id TEXT);",
                down_sql="DROP TABLE test;",
            ),
            Migration(
                version="002",
                name="add_column",
                description="Add column",
                up_sql="ALTER TABLE test ADD COLUMN name TEXT;",
                down_sql="ALTER TABLE test DROP COLUMN name;",
            ),
            Migration(
                version="003",
                name="add_index",
                description="Add index",
                up_sql="CREATE INDEX idx_test_name ON test(name);",
                down_sql="DROP INDEX idx_test_name;",
            ),
        ]

    def test_get_pending_migrations(self):
        """get_pending_migrations should return unapplied migrations."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        pending = manager.get_pending_migrations()
        assert len(pending) == 3

    def test_up_applies_all(self):
        """up() should apply all pending migrations."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        applied = manager.up()
        assert len(applied) == 3
        assert manager.get_current_version() == "003"

    def test_up_to_target_version(self):
        """up() should apply migrations up to target version."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        applied = manager.up(target_version="002")
        assert len(applied) == 2
        assert manager.get_current_version() == "002"

    def test_down_rollback(self):
        """down() should rollback migrations."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        manager.up()
        rolled_back = manager.down("001")
        assert len(rolled_back) == 2
        assert manager.get_current_version() == "001"

    def test_validate_no_errors(self):
        """validate should return no errors for valid migrations."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        errors = manager.validate()
        assert len(errors) == 0

    def test_validate_checksum_mismatch(self):
        """validate should detect checksum mismatches."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        manager.up()

        # Tamper with a migration
        original = manager._migrations["001"]
        tampered = Migration(
            version="001",
            name="initial_schema",
            description="Initial schema",
            up_sql="CREATE TABLE different (id TEXT);",  # Changed SQL
            down_sql="DROP TABLE different;",
        )
        manager._migrations["001"] = tampered

        errors = manager.validate()
        assert len(errors) > 0
        assert "Checksum mismatch" in errors[0]

    def test_info(self):
        """info should return migration status."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        info = manager.info()
        assert info["total_migrations"] == 3
        assert info["applied_count"] == 0
        assert info["pending_count"] == 3
        assert info["current_version"] is None

    def test_info_after_up(self):
        """info should reflect applied migrations."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        manager = MigrationManager(self._make_migrations(), store, executor)
        manager.up()
        info = manager.info()
        assert info["applied_count"] == 3
        assert info["pending_count"] == 0
        assert info["current_version"] == "003"

    def test_up_failure_rolls_back(self):
        """up() should rollback on failure."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()

        # Create a migration that will fail
        bad_migration = Migration(
            version="001",
            name="bad_migration",
            description="This will fail",
            up_sql="INVALID SQL",
            down_sql="DROP TABLE test;",
        )

        # Override executor to raise on bad SQL
        class FailingExecutor(InMemoryMigrationExecutor):
            def execute(self, sql: str) -> None:
                if "INVALID" in sql:
                    raise RuntimeError("SQL execution failed")
                super().execute(sql)

        manager = MigrationManager([bad_migration], store, FailingExecutor())
        with pytest.raises(PersistenceError, match="failed"):
            manager.up()

        # Migration should not be recorded
        assert manager.get_current_version() is None

    def test_duplicate_versions_detected(self):
        """validate should detect duplicate versions."""
        store = InMemoryMigrationStore()
        executor = InMemoryMigrationExecutor()
        migrations = [
            Migration(
                version="001",
                name="first",
                description="First",
                up_sql="SELECT 1;",
                down_sql="SELECT 1;",
            ),
            Migration(
                version="001",
                name="second",
                description="Second",
                up_sql="SELECT 2;",
                down_sql="SELECT 2;",
            ),
        ]
        manager = MigrationManager(migrations, store, executor)
        errors = manager.validate()
        assert any("Duplicate" in e for e in errors)


class TestInMemoryMigrationStore:
    def test_record_and_retrieve(self):
        """Store should record and retrieve migration records."""
        store = InMemoryMigrationStore()
        record = MigrationRecord(
            version="001",
            name="initial",
            applied_at=Instant.now(),
            applied_by="test",
            checksum="abc123",
            execution_time_ms=10,
        )
        store.record_applied(record)
        records = store.get_applied_migrations()
        assert len(records) == 1
        assert records[0].version == "001"

    def test_get_last_applied_version(self):
        """get_last_applied_version should return highest version."""
        store = InMemoryMigrationStore()
        store.record_applied(MigrationRecord(
            version="001", name="first", applied_at=Instant.now(),
            applied_by="test", checksum="abc", execution_time_ms=10,
        ))
        store.record_applied(MigrationRecord(
            version="002", name="second", applied_at=Instant.now(),
            applied_by="test", checksum="def", execution_time_ms=10,
        ))
        assert store.get_last_applied_version() == "002"

    def test_get_last_applied_version_empty(self):
        """get_last_applied_version should return None for empty store."""
        store = InMemoryMigrationStore()
        assert store.get_last_applied_version() is None

    def test_remove_record(self):
        """remove_record should remove a migration record."""
        store = InMemoryMigrationStore()
        store.record_applied(MigrationRecord(
            version="001", name="first", applied_at=Instant.now(),
            applied_by="test", checksum="abc", execution_time_ms=10,
        ))
        store.remove_record("001")
        assert len(store.get_applied_migrations()) == 0


class TestInMemoryMigrationExecutor:
    def test_execute_records_sql(self):
        """execute should record executed SQL."""
        executor = InMemoryMigrationExecutor()
        executor.execute("CREATE TABLE test (id TEXT);")
        assert len(executor.executed) == 1
        assert "CREATE TABLE" in executor.executed[0]

    def test_transaction_lifecycle(self):
        """Transaction begin/commit/rollback should work."""
        executor = InMemoryMigrationExecutor()
        executor.begin_transaction()
        executor.execute("SELECT 1;")
        executor.commit_transaction()
        assert len(executor.executed) == 1

    def test_rollback_removes_last(self):
        """rollback should remove the last executed statement."""
        executor = InMemoryMigrationExecutor()
        executor.begin_transaction()
        executor.execute("SELECT 1;")
        executor.rollback_transaction()
        assert len(executor.executed) == 0
