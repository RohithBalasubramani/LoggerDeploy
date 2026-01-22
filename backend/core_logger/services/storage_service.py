"""
Storage Service

Handles dynamic table creation, data writes, and database connections
for logging data to external databases.
"""

import threading
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from sqlalchemy import create_engine, text, MetaData, Table, Column, Float, Integer, String, Boolean, DateTime
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Namespace for tables in target databases
NAMESPACE = 'neuract'


class StorageService:
    """
    Singleton service for external database storage.

    Provides connection management, dynamic table creation, and batch writes.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._engines: Dict[str, Engine] = {}
        self._engine_lock = threading.RLock()
        self._initialized = True
        logger.info("StorageService initialized")

    def _build_connection_url(self, provider: str, connection_string: str) -> str:
        """
        Build SQLAlchemy connection URL from provider and connection string.

        Args:
            provider: 'sqlite', 'postgres', 'mysql', or 'mssql'
            connection_string: Provider-specific connection string

        Returns:
            SQLAlchemy connection URL
        """
        if provider == 'sqlite':
            # connection_string is the file path
            return f"sqlite:///{connection_string}"

        elif provider == 'postgres':
            # connection_string format: host:port/database?user=xxx&password=xxx
            # or full URL: postgresql://user:pass@host:port/db
            if connection_string.startswith('postgresql://'):
                return connection_string
            return f"postgresql://{connection_string}"

        elif provider == 'mysql':
            if connection_string.startswith('mysql://'):
                return connection_string
            return f"mysql+pymysql://{connection_string}"

        elif provider == 'mssql':
            if connection_string.startswith('mssql://'):
                return connection_string
            return f"mssql+pyodbc://{connection_string}"

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _get_engine(self, provider: str, connection_string: str) -> Engine:
        """Get or create a SQLAlchemy engine for the given connection."""
        key = f"{provider}:{connection_string}"

        with self._engine_lock:
            engine = self._engines.get(key)
            if engine is not None:
                return engine

            url = self._build_connection_url(provider, connection_string)
            engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self._engines[key] = engine
            logger.info(f"Created engine for {provider}")
            return engine

    def _drop_engine(self, provider: str, connection_string: str) -> None:
        """Close and remove an engine from the pool."""
        key = f"{provider}:{connection_string}"

        with self._engine_lock:
            engine = self._engines.pop(key, None)
            if engine:
                engine.dispose()
                logger.info(f"Disposed engine for {provider}")

    def test_connection(
        self,
        provider: str,
        connection_string: str
    ) -> Tuple[bool, int, str]:
        """
        Test connection to a storage target.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        start = time.perf_counter()

        try:
            engine = self._get_engine(provider, connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            latency = int((time.perf_counter() - start) * 1000)
            return True, latency, ""

        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            self._drop_engine(provider, connection_string)
            return False, latency, str(e)

    def _get_table_name(self, table_name: str, provider: str) -> str:
        """
        Get the full table name with namespace.

        PostgreSQL/MSSQL use schema prefix, SQLite/MySQL use underscore prefix.
        """
        if provider in ('postgres', 'mssql'):
            return f"{NAMESPACE}.{table_name}"
        else:
            return f"{NAMESPACE}__{table_name}"

    def _get_sqlalchemy_type(self, data_type: str):
        """Convert our data type to SQLAlchemy type."""
        type_map = {
            'bool': Boolean,
            'int': Integer,
            'float': Float,
            'string': String(255),
        }
        return type_map.get(data_type, Float)

    def ensure_schema_exists(self, provider: str, connection_string: str) -> None:
        """Ensure the namespace schema exists (for Postgres/MSSQL)."""
        if provider not in ('postgres', 'mssql'):
            return

        engine = self._get_engine(provider, connection_string)

        with engine.connect() as conn:
            if provider == 'postgres':
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {NAMESPACE}"))
            elif provider == 'mssql':
                conn.execute(text(f"""
                    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{NAMESPACE}')
                    BEGIN EXEC('CREATE SCHEMA {NAMESPACE}') END
                """))
            conn.commit()

    def create_table(
        self,
        provider: str,
        connection_string: str,
        table_name: str,
        columns: List[Dict[str, str]]
    ) -> Tuple[bool, str]:
        """
        Create a table in the target database.

        Args:
            provider: Database provider
            connection_string: Connection string
            table_name: Logical table name
            columns: List of column definitions [{key, field_type}, ...]

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.ensure_schema_exists(provider, connection_string)

            engine = self._get_engine(provider, connection_string)
            full_table_name = self._get_table_name(table_name, provider)

            # Build column definitions
            col_defs = [Column('timestamp_utc', DateTime, nullable=False)]
            for col in columns:
                col_type = self._get_sqlalchemy_type(col.get('field_type', 'float'))
                col_defs.append(Column(col['key'], col_type, nullable=True))

            # Create table
            metadata = MetaData()

            if provider in ('postgres', 'mssql'):
                table = Table(table_name, metadata, *col_defs, schema=NAMESPACE)
            else:
                table = Table(f"{NAMESPACE}__{table_name}", metadata, *col_defs)

            metadata.create_all(engine)
            logger.info(f"Created table {full_table_name}")
            return True, ""

        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False, str(e)

    def drop_table(
        self,
        provider: str,
        connection_string: str,
        table_name: str
    ) -> Tuple[bool, str]:
        """Drop a table from the target database."""
        try:
            engine = self._get_engine(provider, connection_string)
            full_table_name = self._get_table_name(table_name, provider)

            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {full_table_name}"))
                conn.commit()

            logger.info(f"Dropped table {full_table_name}")
            return True, ""

        except Exception as e:
            logger.error(f"Failed to drop table {table_name}: {e}")
            return False, str(e)

    def table_exists(
        self,
        provider: str,
        connection_string: str,
        table_name: str
    ) -> bool:
        """Check if a table exists in the target database."""
        try:
            engine = self._get_engine(provider, connection_string)
            full_table_name = self._get_table_name(table_name, provider)

            with engine.connect() as conn:
                if provider == 'postgres':
                    result = conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = '{NAMESPACE}'
                            AND table_name = '{table_name}'
                        )
                    """))
                elif provider == 'mssql':
                    result = conn.execute(text(f"""
                        SELECT CASE WHEN EXISTS (
                            SELECT * FROM INFORMATION_SCHEMA.TABLES
                            WHERE TABLE_SCHEMA = '{NAMESPACE}'
                            AND TABLE_NAME = '{table_name}'
                        ) THEN 1 ELSE 0 END
                    """))
                elif provider == 'mysql':
                    result = conn.execute(text(f"""
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_name = '{NAMESPACE}__{table_name}'
                    """))
                else:  # sqlite
                    result = conn.execute(text(f"""
                        SELECT COUNT(*) FROM sqlite_master
                        WHERE type='table' AND name='{NAMESPACE}__{table_name}'
                    """))

                row = result.fetchone()
                return bool(row[0]) if row else False

        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False

    def insert_row(
        self,
        provider: str,
        connection_string: str,
        table_name: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Insert a single row into a table.

        Args:
            provider: Database provider
            connection_string: Connection string
            table_name: Logical table name
            data: Dictionary of column -> value

        Returns:
            Tuple of (success, error_message)
        """
        try:
            engine = self._get_engine(provider, connection_string)
            full_table_name = self._get_table_name(table_name, provider)

            # Add timestamp if not present
            if 'timestamp_utc' not in data:
                data['timestamp_utc'] = datetime.utcnow()

            columns = ', '.join(data.keys())
            placeholders = ', '.join([f':{k}' for k in data.keys()])

            with engine.connect() as conn:
                conn.execute(
                    text(f"INSERT INTO {full_table_name} ({columns}) VALUES ({placeholders})"),
                    data
                )
                conn.commit()

            return True, ""

        except Exception as e:
            logger.error(f"Failed to insert row into {table_name}: {e}")
            return False, str(e)

    def insert_batch(
        self,
        provider: str,
        connection_string: str,
        table_name: str,
        rows: List[Dict[str, Any]]
    ) -> Tuple[bool, int, str]:
        """
        Insert multiple rows into a table.

        Args:
            provider: Database provider
            connection_string: Connection string
            table_name: Logical table name
            rows: List of row dictionaries

        Returns:
            Tuple of (success, rows_inserted, error_message)
        """
        if not rows:
            return True, 0, ""

        try:
            engine = self._get_engine(provider, connection_string)
            full_table_name = self._get_table_name(table_name, provider)

            # Add timestamp to rows if not present
            now = datetime.utcnow()
            for row in rows:
                if 'timestamp_utc' not in row:
                    row['timestamp_utc'] = now

            # Use first row to determine columns
            columns = list(rows[0].keys())
            col_str = ', '.join(columns)
            placeholders = ', '.join([f':{k}' for k in columns])

            with engine.connect() as conn:
                conn.execute(
                    text(f"INSERT INTO {full_table_name} ({col_str}) VALUES ({placeholders})"),
                    rows
                )
                conn.commit()

            return True, len(rows), ""

        except Exception as e:
            logger.error(f"Failed to insert batch into {table_name}: {e}")
            return False, 0, str(e)

    def discover_tables(
        self,
        provider: str,
        connection_string: str
    ) -> List[str]:
        """
        Discover existing neuract tables in the target database.

        Returns:
            List of table names (without namespace prefix)
        """
        try:
            engine = self._get_engine(provider, connection_string)

            with engine.connect() as conn:
                if provider == 'postgres':
                    result = conn.execute(text(f"""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = '{NAMESPACE}'
                    """))
                elif provider == 'mssql':
                    result = conn.execute(text(f"""
                        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = '{NAMESPACE}'
                    """))
                elif provider == 'mysql':
                    result = conn.execute(text(f"""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_name LIKE '{NAMESPACE}__%%'
                    """))
                else:  # sqlite
                    result = conn.execute(text(f"""
                        SELECT name FROM sqlite_master
                        WHERE type='table' AND name LIKE '{NAMESPACE}__%%'
                    """))

                tables = []
                for row in result:
                    name = row[0]
                    # Strip namespace prefix
                    if name.startswith(f"{NAMESPACE}__"):
                        name = name[len(f"{NAMESPACE}__"):]
                    tables.append(name)

                return tables

        except Exception as e:
            logger.error(f"Failed to discover tables: {e}")
            return []

    def dispose_all(self) -> None:
        """Dispose all database engines."""
        with self._engine_lock:
            for key in list(self._engines.keys()):
                engine = self._engines.pop(key, None)
                if engine:
                    engine.dispose()
        logger.info("Disposed all storage engines")


# Singleton instance
storage_service = StorageService()
