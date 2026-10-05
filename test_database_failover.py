import unittest
from threading import Lock
from types import SimpleNamespace

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

import app.core.database as database
import app.models


class DatabaseFailoverTests(unittest.TestCase):
    def setUp(self):
        self.original_state = (
            database._primary_engine,
            database._offline_engine,
            database._active_engine,
            database._using_offline_database,
            database._engine_lock,
            database._check_connection,
        )
        self.primary_engine = SimpleNamespace(
            dialect=SimpleNamespace(name="postgresql")
        )
        self.offline_engine = create_engine("sqlite:///:memory:")
        database._primary_engine = self.primary_engine
        database._offline_engine = self.offline_engine
        database._active_engine = self.primary_engine
        database._using_offline_database = False
        database._engine_lock = Lock()

    def tearDown(self):
        (
            database._primary_engine,
            database._offline_engine,
            database._active_engine,
            database._using_offline_database,
            database._engine_lock,
            database._check_connection,
        ) = self.original_state
        self.offline_engine.dispose()

    def test_fails_over_and_creates_same_schema_locally(self):
        def check_connection(engine):
            if engine is self.primary_engine:
                raise SQLAlchemyError("simulated hosted database outage")

        database._check_connection = check_connection

        active_engine = database.get_active_engine()

        self.assertIs(active_engine, self.offline_engine)
        self.assertTrue(database.is_using_offline_database())
        inspector = inspect(active_engine)
        self.assertEqual(
            set(inspector.get_table_names()),
            set(database.Base.metadata.tables),
        )
        for table in database.Base.metadata.sorted_tables:
            self.assertEqual(
                {column["name"] for column in inspector.get_columns(table.name)},
                set(table.columns.keys()),
                table.name,
            )

    def test_offline_choice_is_pinned_until_process_restart(self):
        primary_checks = 0

        def check_connection(engine):
            nonlocal primary_checks
            if engine is self.primary_engine:
                primary_checks += 1
                if primary_checks == 1:
                    raise SQLAlchemyError("simulated hosted database outage")

        database._check_connection = check_connection

        first_engine = database.get_active_engine()
        second_engine = database.get_active_engine()

        self.assertIs(first_engine, self.offline_engine)
        self.assertIs(second_engine, self.offline_engine)
        self.assertEqual(primary_checks, 1)


if __name__ == "__main__":
    unittest.main()
