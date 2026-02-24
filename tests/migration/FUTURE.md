# Migration Testing Framework - Implementation Plan

## Overview

This document outlines a comprehensive strategy for testing database migrations to prevent data loss and ensure data integrity during schema changes. The framework focuses on automated pytest-based tests that verify migrations individually before they reach production.

## Core Principles

### Testing Focus Areas

1. **Data Transformation Accuracy**: Ensure data is correctly transformed during schema changes (e.g., renaming tables, migrating column values)
2. **Foreign Key Integrity**: Verify all relationships remain intact and no orphaned records are created
3. **Backward Compatibility**: Test that migrations can be rolled back safely without data loss
4. **Production Data Scenarios**: Use realistic data volumes and edge cases that mirror production

### Test Philosophy

- Each migration test runs in isolation with a clean database state
- Tests should be deterministic and repeatable
- Use production-like test data to catch edge cases
- Tests should be fast enough for CI/CD (target: < 30 seconds per migration)
- All tests run against local Supabase instance

## Directory Structure

```
tests/migration/
├── README.md                          # User guide for writing migration tests
├── conftest.py                        # Migration-specific pytest fixtures
├── helpers/
│   ├── __init__.py
│   ├── migration_runner.py            # Core migration execution utilities
│   ├── data_generator.py              # Generate realistic test data
│   ├── assertion_helpers.py           # Common assertion patterns
│   └── db_state.py                    # Database state management
├── test_migrations/
│   ├── __init__.py
│   ├── test_migration_20250915000002.py  # Example: add NOT NULL constraint
│   ├── test_migration_20250922000004.py  # Example: enum value migration
│   └── test_migration_20251013000003.py  # Example: table/column rename
└── fixtures/
    └── sample_data.py                 # Reusable test data generators
```

## Component Details

### 1. Core Testing Infrastructure

#### `conftest.py`

Provides migration-specific fixtures:

```python
@pytest.fixture
def migration_db():
    """
    Create a fresh isolated database for migration testing.
    Uses Supabase local instance with unique schema per test.
    Cleans up after test completes.
    """
    pass

@pytest.fixture
def migration_runner(migration_db):
    """
    Helper object to run migrations forward and backward.
    Tracks current migration state and provides utilities.
    """
    pass

@pytest.fixture
def data_generator(migration_db):
    """
    Helper to create realistic production-like test data.
    Provides methods to generate users, greetings, etc.
    """
    pass

@pytest.fixture
def db_inspector(migration_db):
    """
    Utility to inspect database state (tables, columns, constraints, etc.)
    Used for assertions about schema changes.
    """
    pass
```

#### `helpers/migration_runner.py`

Core migration execution logic:

```python
class MigrationRunner:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_state = None
        self.migration_history = []

    def reset_to_migration(self, migration_id: str):
        """Reset DB to state just before specified migration."""
        pass

    def apply_migration(self, migration_id: str):
        """Apply a single migration forward."""
        pass

    def rollback_migration(self, migration_id: str):
        """Rollback a single migration."""
        pass

    def get_migration_list(self) -> List[str]:
        """Get ordered list of all migrations."""
        pass

    def capture_state_snapshot(self) -> Dict:
        """Capture current DB state for comparison."""
        pass
```

#### `helpers/data_generator.py`

Generate realistic test data:

```python
class DataGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.created_objects = []  # Track for cleanup/verification

    def create_user(self, **kwargs) -> dict:
        """Create a user with realistic data."""
        pass

    def create_greeting(self, user_id, **kwargs) -> dict:
        """Create a greeting with all required relationships."""
        pass

    def create_greeting_with_metadata(self, **kwargs) -> dict:
        """
        Create a complete greeting scenario with related records.
        Useful for testing migrations that affect multiple tables.
        """
        pass

    def generate_edge_cases(self) -> List[dict]:
        """
        Generate edge case data scenarios:
        - Orphaned records
        - NULL values
        - Large data volumes
        - Unicode/special characters
        """
        pass
```

#### `helpers/assertion_helpers.py`

Common assertion patterns:

```python
class MigrationAssertions:
    def __init__(self, db_connection):
        self.db = db_connection

    def assert_table_exists(self, table_name: str):
        """Verify table exists."""
        pass

    def assert_table_renamed(self, old_name: str, new_name: str):
        """Verify table was renamed correctly."""
        pass

    def assert_column_exists(self, table: str, column: str):
        """Verify column exists in table."""
        pass

    def assert_foreign_key_intact(self, table: str, fk_name: str):
        """Verify foreign key constraint still exists and works."""
        pass

    def assert_row_count_preserved(self, table: str, expected_count: int):
        """Verify no data loss (row count unchanged)."""
        pass

    def assert_data_transformation_correct(
        self,
        table: str,
        transformation_fn: Callable,
        sample_rows: List[dict]
    ):
        """Verify data was transformed correctly according to function."""
        pass

    def assert_triggers_exist(self, table: str, trigger_names: List[str]):
        """Verify triggers were recreated after migration."""
        pass

    def assert_rls_policies_exist(self, table: str, policy_names: List[str]):
        """Verify RLS policies are in place."""
        pass

    def assert_indexes_exist(self, table: str, index_names: List[str]):
        """Verify indexes were recreated."""
        pass

    def assert_data_checksum_matches(
        self,
        table: str,
        columns: List[str],
        expected_checksum: str
    ):
        """Verify data integrity via checksum."""
        pass
```

#### `helpers/db_state.py`

Database state management:

```python
class DatabaseState:
    """Capture and compare database states."""

    def __init__(self, db_connection):
        self.db = db_connection

    def capture(self) -> dict:
        """
        Capture complete DB state including:
        - Schema (tables, columns, types)
        - Constraints (FK, unique, check)
        - Indexes
        - Triggers
        - RLS policies
        - Row counts and data checksums per table
        """
        pass

    def compare(self, state1: dict, state2: dict) -> dict:
        """
        Compare two states and return differences.
        Returns structured diff showing:
        - Tables added/removed/renamed
        - Columns added/removed/modified
        - Constraints changed
        - Data differences
        """
        pass

    def assert_equivalent(
        self,
        state1: dict,
        state2: dict,
        ignore_tables: List[str] = None
    ):
        """
        Assert two states are equivalent (for rollback testing).
        Ignores metadata tables by default.
        """
        pass
```

### 2. Base Test Class

#### `base_migration_test.py`

Common patterns for migration tests:

```python
class BaseMigrationTest:
    """
    Base class for migration tests.
    Subclass this to test specific migrations.
    """

    # Override in subclass
    MIGRATION_ID = None  # e.g., "20251013000003"
    MIGRATION_NAME = None  # e.g., "rename_old_table_to_new_table"

    def setup_method(self):
        """Setup run before each test method."""
        self.runner = None  # Set by fixtures
        self.generator = None
        self.assertions = None

    def setup_pre_migration_data(self) -> dict:
        """
        Override to create test data before migration.
        Should return dict with references to created objects.
        """
        raise NotImplementedError

    def verify_migration_forward(self, pre_data: dict):
        """
        Override to verify migration applied correctly.
        Check schema changes and data transformations.
        """
        raise NotImplementedError

    def verify_migration_rollback(self, pre_data: dict):
        """
        Override to verify rollback restored original state.
        Check data integrity and schema restoration.
        """
        raise NotImplementedError

    def test_migration_forward(self, migration_runner, data_generator, db_assertions):
        """Test applying migration forward."""
        # Setup
        self.runner = migration_runner
        self.generator = data_generator
        self.assertions = db_assertions

        # Reset to just before this migration
        self.runner.reset_to_migration(self.MIGRATION_ID)

        # Create test data
        pre_data = self.setup_pre_migration_data()

        # Capture state before
        state_before = self.runner.capture_state_snapshot()

        # Apply migration
        self.runner.apply_migration(self.MIGRATION_ID)

        # Verify
        self.verify_migration_forward(pre_data)

    def test_migration_rollback(self, migration_runner, data_generator, db_assertions):
        """Test rolling back migration."""
        # Setup
        self.runner = migration_runner
        self.generator = data_generator
        self.assertions = db_assertions

        # Apply migration first
        self.runner.reset_to_migration(self.MIGRATION_ID)
        pre_data = self.setup_pre_migration_data()
        state_before = self.runner.capture_state_snapshot()
        self.runner.apply_migration(self.MIGRATION_ID)

        # Rollback
        self.runner.rollback_migration(self.MIGRATION_ID)
        state_after_rollback = self.runner.capture_state_snapshot()

        # Verify rollback
        self.verify_migration_rollback(pre_data)

        # States should be equivalent
        self.assertions.assert_states_equivalent(state_before, state_after_rollback)

    def test_migration_with_edge_cases(self, migration_runner, data_generator):
        """Test migration with edge case data."""
        self.runner = migration_runner
        self.generator = data_generator

        # Reset and create edge case data
        self.runner.reset_to_migration(self.MIGRATION_ID)
        edge_cases = self.generator.generate_edge_cases()

        # Apply migration - should not fail
        self.runner.apply_migration(self.MIGRATION_ID)

        # Verify data integrity preserved
        self.verify_edge_cases_handled(edge_cases)

    def test_migration_foreign_key_integrity(self, migration_runner, data_generator):
        """Test all foreign keys remain intact."""
        self.runner = migration_runner
        self.generator = data_generator

        # Setup with related data
        self.runner.reset_to_migration(self.MIGRATION_ID)
        pre_data = self.setup_pre_migration_data()

        # Capture all FK relationships before
        fks_before = self.runner.get_foreign_keys()

        # Apply migration
        self.runner.apply_migration(self.MIGRATION_ID)

        # Verify FK integrity
        fks_after = self.runner.get_foreign_keys()
        self.verify_foreign_key_integrity(fks_before, fks_after, pre_data)
```

### 3. Example Migration Test

#### `test_migration_20251013000003.py`

Complete example for a table/column rename migration:

```python
from tests.migration.base_migration_test import BaseMigrationTest

class TestMigration20251013000003(BaseMigrationTest):
    """
    Test table/column rename migration.

    This migration:
    - Renames tables: old_items → new_items
    - Renames columns: old_ref_id → new_ref_id
    - Updates enum constraints: 'old_role' → 'new_role'
    - Renames all related constraints, indexes, triggers
    - Updates RLS policies
    """

    MIGRATION_ID = "20251013000003"
    MIGRATION_NAME = "rename_old_items_to_new_items"

    def setup_pre_migration_data(self) -> dict:
        """Create test data before migration."""
        # Create users
        owner = self.generator.create_user(
            email="owner@test.com",
            full_name="Test Owner"
        )
        member = self.generator.create_user(
            email="member@test.com",
            full_name="Test Member"
        )

        # Create parent record
        parent = self.db.execute("""
            INSERT INTO parents (owner_id, title)
            VALUES (%s, 'Test Parent')
            RETURNING *
        """, (owner['id'],))

        # Create old_items record
        item = self.db.execute("""
            INSERT INTO old_items
            (parent_id, old_ref_id, status)
            VALUES (%s, %s, 'active')
            RETURNING *
        """, (parent['id'], member['id']))

        # Create history entry with old role value
        history = self.db.execute("""
            INSERT INTO audit_log
            (parent_id, action_type, user_id, role)
            VALUES (%s, 'item_created', %s, 'old_role')
            RETURNING *
        """, (parent['id'], member['id']))

        return {
            'owner': owner,
            'member': member,
            'parent': parent,
            'item': item,
            'history': history
        }

    def verify_migration_forward(self, pre_data: dict):
        """Verify migration renamed everything correctly."""

        # 1. Verify tables renamed
        self.assertions.assert_table_exists('new_items')
        self.assertions.assert_table_not_exists('old_items')

        # 2. Verify columns renamed
        self.assertions.assert_column_exists('new_items', 'new_ref_id')
        self.assertions.assert_column_not_exists('new_items', 'old_ref_id')

        # 3. Verify data preserved
        item = self.db.execute("""
            SELECT * FROM new_items
            WHERE new_ref_id = %s
        """, (pre_data['member']['id'],))

        assert item is not None
        assert item['status'] == 'active'

        # 4. Verify history updated
        history = self.db.execute("""
            SELECT * FROM audit_log WHERE id = %s
        """, (pre_data['history']['id'],))

        assert history['role'] == 'new_role'

        # 5. Verify constraints renamed
        self.assertions.assert_constraint_exists(
            'new_items', 'new_items_pkey'
        )
        self.assertions.assert_foreign_key_exists(
            'new_items', 'new_items_new_ref_id_fkey'
        )

        # 6. Verify indexes renamed
        self.assertions.assert_index_exists('idx_new_items_new_ref_id')

        # 7. Verify triggers renamed
        self.assertions.assert_trigger_exists(
            'new_items', 'on_new_item_created'
        )

        # 8. Verify RLS policies updated
        self.assertions.assert_policy_exists(
            'new_items', 'Users can view their own items'
        )

        # 9. Verify enum constraint
        constraint = self.db.execute("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'check_role'
        """)
        assert 'new_role' in constraint['check_clause']
        assert 'old_role' not in constraint['check_clause']

    def verify_migration_rollback(self, pre_data: dict):
        """Verify rollback restored original state."""

        # 1. Verify tables restored
        self.assertions.assert_table_exists('old_items')
        self.assertions.assert_table_not_exists('new_items')

        # 2. Verify columns restored
        self.assertions.assert_column_exists('old_items', 'old_ref_id')

        # 3. Verify data preserved
        item = self.db.execute("""
            SELECT * FROM old_items
            WHERE old_ref_id = %s
        """, (pre_data['member']['id'],))

        assert item is not None

        # 4. Verify history restored
        history = self.db.execute("""
            SELECT * FROM audit_log WHERE id = %s
        """, (pre_data['history']['id'],))

        assert history['role'] == 'old_role'
```

### 4. Testing Utilities

#### `helpers/migration_runner.py` (Implementation Details)

```python
import subprocess
from pathlib import Path
from typing import List, Optional
import re

class MigrationRunner:
    """Execute Supabase migrations programmatically."""

    def __init__(self, db_connection_string: str):
        self.db_url = db_connection_string
        self.migrations_dir = Path("supabase/migrations")
        self.current_migration = None

    def get_migration_list(self) -> List[str]:
        """Get ordered list of all migrations."""
        migrations = []
        for file in sorted(self.migrations_dir.glob("*.sql")):
            # Extract migration ID from filename
            match = re.match(r'(\d+)_.*\.sql', file.name)
            if match:
                migrations.append(match.group(1))
        return migrations

    def get_migration_path(self, migration_id: str) -> Path:
        """Get file path for migration."""
        for file in self.migrations_dir.glob(f"{migration_id}_*.sql"):
            return file
        raise ValueError(f"Migration {migration_id} not found")

    def reset_to_migration(self, migration_id: str):
        """
        Reset database to state just before specified migration.
        Uses Supabase CLI or direct SQL execution.
        """
        migrations = self.get_migration_list()
        target_index = migrations.index(migration_id)

        # Apply all migrations up to (but not including) target
        for i, mig_id in enumerate(migrations):
            if i < target_index:
                self._apply_migration_sql(mig_id)
            else:
                break

        self.current_migration = migrations[target_index - 1] if target_index > 0 else None

    def apply_migration(self, migration_id: str):
        """Apply a single migration forward."""
        migration_file = self.get_migration_path(migration_id)

        # Read and execute SQL
        with open(migration_file, 'r') as f:
            sql = f.read()

        # Execute against database
        self._execute_sql(sql)
        self.current_migration = migration_id

    def rollback_migration(self, migration_id: str):
        """
        Rollback a migration.
        For Supabase, this requires a reverse migration file.
        """
        # Look for corresponding down migration or generate reverse SQL
        # This is migration-specific logic
        raise NotImplementedError(
            "Rollback requires reverse migration SQL. "
            "Consider generating or maintaining down migrations."
        )

    def _execute_sql(self, sql: str):
        """Execute SQL against the database."""
        # Use psycopg2 or subprocess to run SQL
        pass

    def capture_state_snapshot(self) -> dict:
        """Capture current database state."""
        from helpers.db_state import DatabaseState
        return DatabaseState(self.db_url).capture()
```

### 5. Test Execution

#### Running Tests

```bash
# Run all migration tests
pytest tests/migration/ -v

# Run specific migration test
pytest tests/migration/test_migrations/test_migration_20251013000003.py -v

# Run with detailed output
pytest tests/migration/ -vv --tb=short

# Run only forward migration tests
pytest tests/migration/ -k "forward" -v

# Run only rollback tests
pytest tests/migration/ -k "rollback" -v
```

#### Integration with CI/CD

Add to `.github/workflows/test.yml`:

```yaml
- name: Run Migration Tests
  run: |
    # Start local Supabase
    supabase start

    # Run migration tests
    pytest tests/migration/ -v --tb=short

    # Stop Supabase
    supabase stop
```

### 6. Documentation

#### `tests/migration/README.md`

````markdown
# Migration Testing Guide

## When to Write Migration Tests

Write a migration test when your migration:

1. **Transforms existing data** (renaming, restructuring, calculating new values)
2. **Modifies relationships** (foreign keys, junction tables)
3. **Changes constraints** (NOT NULL, unique, check constraints)
4. **Affects multiple tables** (complex migrations with cascading changes)
5. **Could cause data loss** if implemented incorrectly

## How to Write a Migration Test

### Step 1: Create Test File

Create `test_migration_YYYYMMDDNNNNNN.py` where the timestamp matches your migration.

### Step 2: Subclass BaseMigrationTest

```python
from tests.migration.base_migration_test import BaseMigrationTest

class TestMigrationXXXXXX(BaseMigrationTest):
    MIGRATION_ID = "YYYYMMDDNNNNNN"
    MIGRATION_NAME = "descriptive_name"
```
````

### Step 3: Implement setup_pre_migration_data()

Create realistic test data that will be affected by your migration:

```python
def setup_pre_migration_data(self) -> dict:
    # Create all data that exists BEFORE migration
    # Return dict with references for verification
    pass
```

### Step 4: Implement verify_migration_forward()

Verify that migration correctly transformed the data:

```python
def verify_migration_forward(self, pre_data: dict):
    # Assert schema changes (tables, columns)
    # Assert data transformations
    # Assert constraints, indexes, triggers
    # Assert foreign key integrity
    pass
```

### Step 5: Implement verify_migration_rollback()

Verify that rollback restores original state:

```python
def verify_migration_rollback(self, pre_data: dict):
    # Assert schema restored
    # Assert data unchanged from original
    pass
```

## Common Patterns

### Testing Table Renames

```python
def verify_migration_forward(self, pre_data: dict):
    self.assertions.assert_table_exists('new_table_name')
    self.assertions.assert_table_not_exists('old_table_name')

    # Verify data migrated
    count = self.db.execute("SELECT COUNT(*) FROM new_table_name")
    assert count == pre_data['expected_count']
```

### Testing Data Transformations

```python
def verify_migration_forward(self, pre_data: dict):
    # Verify transformation logic
    for old_record in pre_data['records']:
        new_record = self.db.fetch_one(
            "SELECT * FROM table WHERE id = %s",
            (old_record['id'],)
        )
        assert new_record['new_column'] == transform(old_record['old_column'])
```

### Testing Foreign Key Integrity

```python
def verify_migration_forward(self, pre_data: dict):
    # Verify FK constraint exists
    self.assertions.assert_foreign_key_exists('table', 'fk_name')

    # Verify FK relationships still valid
    parent_id = pre_data['parent']['id']
    children = self.db.fetch_all(
        "SELECT * FROM children WHERE parent_id = %s",
        (parent_id,)
    )
    assert len(children) == pre_data['expected_children_count']
```

## Best Practices

1. **Use realistic data**: Create data that mirrors production scenarios
2. **Test edge cases**: NULL values, empty strings, large volumes
3. **Verify constraints**: Check all constraints still enforced after migration
4. **Test rollback**: Always test that rollback works correctly
5. **Keep tests fast**: Use minimal data needed to verify correctness
6. **Document assumptions**: Comment why specific data is created

## Example: Complete Migration Test

See `test_migration_20251013000003.py` for a comprehensive example that tests:

- Table and column renames
- Data preservation
- Constraint and enum updates
- Index and trigger recreation
- RLS policy updates
- Rollback verification

```

## Implementation Phases

### Phase 1: Core Infrastructure (Priority 1)
1. Create `tests/migration/` directory structure
2. Implement `conftest.py` with basic fixtures
3. Implement `helpers/migration_runner.py` with essential methods
4. Implement `helpers/assertion_helpers.py` with common assertions
5. Create `base_migration_test.py` base class

**Estimated effort**: 4-6 hours

### Phase 2: Example Implementation (Priority 1)
1. Choose one complex migration as a reference implementation
2. Implement complete test following all patterns
3. Verify test catches actual issues
4. Document lessons learned

**Estimated effort**: 3-4 hours

### Phase 3: Additional Utilities (Priority 2)
1. Implement `helpers/data_generator.py`
2. Implement `helpers/db_state.py`
3. Add rollback support to `migration_runner.py`
4. Create reusable fixtures in `fixtures/sample_data.py`

**Estimated effort**: 3-4 hours

### Phase 4: Documentation & Integration (Priority 2)
1. Write comprehensive `README.md`
2. Add migration test section to main CLAUDE.md
3. Integrate with CI/CD pipeline
4. Create template for new migration tests

**Estimated effort**: 2-3 hours

### Phase 5: Additional Tests (Priority 3)
1. Add tests for 2-3 more complex migrations
2. Refine patterns based on experience
3. Build library of reusable test data scenarios

**Estimated effort**: 4-6 hours per migration

## Success Metrics

- ✅ At least one fully tested complex migration
- ✅ All four focus areas verified (transformation, FK integrity, rollback, production scenarios)
- ✅ Tests run in < 30 seconds
- ✅ Tests integrated into CI/CD
- ✅ Clear documentation for adding new tests
- ✅ Team can write new migration tests independently

## Future Enhancements

1. **Automatic rollback generation**: Tool to generate reverse migrations
2. **Performance testing**: Time migrations on large datasets
3. **Production data anonymization**: Tool to create test data from prod
4. **Visual diff tool**: Show schema changes visually
5. **Migration linting**: Detect common migration anti-patterns
6. **Parallel test execution**: Run migration tests in parallel
7. **Snapshot testing**: Store/compare database state snapshots

---

**Next Steps**: Start with Phase 1 to build core infrastructure, then implement Phase 2 example to validate the approach.
```
