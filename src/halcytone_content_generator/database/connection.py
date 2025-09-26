"""
Database Connection Management
Handles database connectivity, session management, and connection pooling
"""

import logging
import asyncio
from typing import Optional, AsyncGenerator, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, MetaData, text, event, pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from .config import get_database_settings, DatabaseType

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages database connections with support for both sync and async operations
    """

    def __init__(self, settings=None):
        """
        Initialize database connection manager

        Args:
            settings: DatabaseSettings instance (uses default if not provided)
        """
        self.settings = settings or get_database_settings()
        self._engine: Optional[Any] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[sessionmaker] = None
        self._async_sessionmaker: Optional[async_sessionmaker] = None
        self._read_engine: Optional[Any] = None
        self._read_async_engine: Optional[AsyncEngine] = None
        self.is_connected = False

    def get_engine(self) -> Any:
        """
        Get or create synchronous database engine

        Returns:
            SQLAlchemy engine instance
        """
        if self._engine is None:
            database_url = self.settings.get_database_url()

            # Choose pool class based on database type
            if self.settings.DATABASE_TYPE == DatabaseType.SQLITE:
                pool_class = NullPool  # SQLite doesn't benefit from connection pooling
            else:
                pool_class = QueuePool

            # Create engine with production-ready settings
            self._engine = create_engine(
                database_url,
                poolclass=pool_class,
                **self.settings.get_pool_args()
            )

            # Add event listeners for monitoring
            if self.settings.DATABASE_ECHO_POOL:
                self._setup_pool_monitoring(self._engine)

            logger.info("Synchronous database engine created")

        return self._engine

    async def get_async_engine(self) -> AsyncEngine:
        """
        Get or create asynchronous database engine

        Returns:
            Async SQLAlchemy engine instance
        """
        if self._async_engine is None:
            database_url = self.settings.get_async_database_url()

            # Choose pool class based on database type
            if self.settings.DATABASE_TYPE == DatabaseType.SQLITE:
                pool_class = NullPool
            else:
                pool_class = QueuePool

            # Create async engine
            self._async_engine = create_async_engine(
                database_url,
                poolclass=pool_class,
                **self.settings.get_pool_args()
            )

            logger.info("Asynchronous database engine created")

        return self._async_engine

    def get_session_factory(self) -> sessionmaker:
        """
        Get synchronous session factory

        Returns:
            Session factory for creating database sessions
        """
        if self._sessionmaker is None:
            engine = self.get_engine()
            self._sessionmaker = sessionmaker(
                bind=engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )

        return self._sessionmaker

    async def get_async_session_factory(self) -> async_sessionmaker:
        """
        Get asynchronous session factory

        Returns:
            Async session factory for creating database sessions
        """
        if self._async_sessionmaker is None:
            engine = await self.get_async_engine()
            self._async_sessionmaker = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )

        return self._async_sessionmaker

    def get_session(self) -> Session:
        """
        Create a new synchronous database session

        Returns:
            Database session
        """
        factory = self.get_session_factory()
        return factory()

    async def get_async_session(self) -> AsyncSession:
        """
        Create a new asynchronous database session

        Returns:
            Async database session
        """
        factory = await self.get_async_session_factory()
        return factory()

    @asynccontextmanager
    async def async_session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions

        Yields:
            Database session with automatic cleanup
        """
        session = await self.get_async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def session_scope(self):
        """
        Context manager for synchronous database sessions

        Yields:
            Database session with automatic cleanup
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def init_database(self) -> bool:
        """
        Initialize database connection and optionally create tables

        Returns:
            True if initialization successful
        """
        try:
            # Test connection
            engine = await self.get_async_engine()

            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()

            self.is_connected = True
            logger.info("Database connection initialized successfully")

            # Run migrations if configured
            if self.settings.DATABASE_AUTO_MIGRATE:
                await self.run_migrations()

            return True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.is_connected = False
            return False

    async def close(self):
        """
        Close all database connections
        """
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None

        if self._engine:
            self._engine.dispose()
            self._engine = None

        if self._read_async_engine:
            await self._read_async_engine.dispose()
            self._read_async_engine = None

        if self._read_engine:
            self._read_engine.dispose()
            self._read_engine = None

        self._sessionmaker = None
        self._async_sessionmaker = None
        self.is_connected = False

        logger.info("Database connections closed")

    async def health_check(self) -> dict:
        """
        Perform database health check

        Returns:
            Health check results
        """
        health = {
            'connected': False,
            'database_type': self.settings.DATABASE_TYPE.value,
            'pool_size': self.settings.DATABASE_POOL_SIZE,
            'response_time_ms': None,
            'error': None
        }

        try:
            import time
            start = time.time()

            engine = await self.get_async_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()

            elapsed = (time.time() - start) * 1000
            health['connected'] = True
            health['response_time_ms'] = round(elapsed, 2)

            # Get pool statistics if available
            if hasattr(engine.pool, 'size'):
                health['pool_stats'] = {
                    'size': engine.pool.size(),
                    'checked_in': engine.pool.checkedin(),
                    'checked_out': engine.pool.checkedout(),
                    'overflow': engine.pool.overflow(),
                    'total': engine.pool.total()
                }

        except Exception as e:
            health['error'] = str(e)
            logger.error(f"Database health check failed: {e}")

        return health

    async def run_migrations(self):
        """
        Run database migrations using Alembic
        """
        try:
            from alembic import command
            from alembic.config import Config

            # Configure Alembic
            alembic_cfg = Config()
            alembic_cfg.set_main_option(
                "script_location",
                self.settings.DATABASE_MIGRATION_DIR
            )
            alembic_cfg.set_main_option(
                "sqlalchemy.url",
                self.settings.get_alembic_url()
            )

            # Run migrations
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")

        except ImportError:
            logger.warning("Alembic not installed, skipping migrations")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

    def _setup_pool_monitoring(self, engine):
        """
        Set up connection pool monitoring events

        Args:
            engine: SQLAlchemy engine to monitor
        """

        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug(f"Pool connection established: {id(dbapi_conn)}")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug(f"Connection checked out from pool: {id(dbapi_conn)}")

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            logger.debug(f"Connection returned to pool: {id(dbapi_conn)}")

    def get_read_replica_engine(self):
        """
        Get read replica engine for read operations

        Returns:
            Engine connected to read replica
        """
        if not self.settings.DATABASE_USE_READ_REPLICA:
            return self.get_engine()

        if self._read_engine is None and self.settings.DATABASE_READ_REPLICA_URL:
            url = self.settings.DATABASE_READ_REPLICA_URL.get_secret_value()
            self._read_engine = create_engine(
                url,
                **self.settings.get_pool_args()
            )
            logger.info("Read replica engine created")

        return self._read_engine or self.get_engine()

    async def get_read_replica_async_engine(self):
        """
        Get async read replica engine

        Returns:
            Async engine connected to read replica
        """
        if not self.settings.DATABASE_USE_READ_REPLICA:
            return await self.get_async_engine()

        if self._read_async_engine is None and self.settings.DATABASE_READ_REPLICA_URL:
            # Convert URL to async format
            url = self.settings.DATABASE_READ_REPLICA_URL.get_secret_value()
            # Apply async driver conversions...
            self._read_async_engine = create_async_engine(
                url,
                **self.settings.get_pool_args()
            )
            logger.info("Async read replica engine created")

        return self._read_async_engine or await self.get_async_engine()


class DatabaseSessionManager:
    """
    Manages database sessions for dependency injection
    """

    def __init__(self, connection: Optional[DatabaseConnection] = None):
        """
        Initialize session manager

        Args:
            connection: DatabaseConnection instance
        """
        self.connection = connection or DatabaseConnection()

    async def __aenter__(self) -> AsyncSession:
        """Async context manager entry"""
        self.session = await self.connection.get_async_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_database() -> DatabaseConnection:
    """
    Get global database connection instance

    Returns:
        DatabaseConnection instance
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Yields:
        Database session
    """
    db = get_database()
    async with db.async_session_scope() as session:
        yield session


async def init_database() -> bool:
    """
    Initialize global database connection

    Returns:
        True if successful
    """
    db = get_database()
    return await db.init_database()


async def close_database():
    """
    Close global database connection
    """
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None