"""
Transaction Session Management for SQLAlchemy
============================================

Overview
--------
This module implements an advanced transaction management approach for SQLAlchemy that addresses key challenges in database operations and session handling.

Key Objectives
--------------
* Defer all database commits until the end of a request
* Maintain existing code without modifications
* Ensure atomic database operations (all-or-nothing approach)

Core Concept
------------
The module introduces a sophisticated mechanism to intercept commit calls without altering existing code, providing a more robust and predictable database transaction workflow.

Comparison: Traditional vs. Advanced Session Management
-------------------------------------------------------

Traditional SQLAlchemy Session
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Immediate commit for each database operation
* Potential for partial updates
* Risk of inconsistent database state

TxAsyncSession Approach
^^^^^^^^^^^^^^^^^^^^^^
* Intercepts all commit() calls
* Allows commits only during final commit phase
* Guarantees atomic operations
* Ensures all changes are applied together or not at all

Implementation Details
---------------------

Commit Interception Mechanism
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. During normal operations: Commit calls are intercepted
2. During final commit: One comprehensive database write occurs
3. Ensures complete transaction integrity

Usage Examples
--------------

Traditional SQLAlchemy Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    # Multiple commits, potential partial updates
    await create_user(session)      # Commits immediately
    await update_profile(session)   # Commits immediately
    await send_welcome(session)     # Commits immediately

Transaction Management Solution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    async with get_transactional_session() as session:
        await create_user(session)      # Commit intercepted
        await update_profile(session)   # Commit intercepted
        await send_welcome(session)     # Commit intercepted
        # All changes committed atomically at context exit

FastAPI Integration Example
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    @router.post("/")
    async def endpoint(session: TxAsyncSession = Depends(get_tx_session())):
        # Database operations with deferred commits
        await db_operation_1(session)
        await db_operation_2(session)
        # Commits handled automatically on successful completion

Primary Use Cases
-----------------
* Complex multi-step database operations
* Maintaining strict data consistency
* Preventing partial database updates
* Preserving existing code structure

Technical Highlights
--------------------
* Transparent to existing code
* Zero modification of existing methods required
* Single atomic commit at transaction conclusion
* Seamless integration with async database workflows
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class TxAsyncSession(AsyncSession):
    """Transactional async session that defers commits until explicitly requested.

    This class extends SQLAlchemy's AsyncSession to provide atomic transaction support
    without requiring changes to existing code. It works by intercepting commit()
    calls and deferring them until the final commit at the end of the transaction.

    Key attributes:
        _commit_on_exit: Whether to commit changes when the session exits
        _is_committing: Flag to control when actual commits are allowed
    """

    def __init__(self, *args, **kwargs):
        """Initialize the transactional session."""
        super().__init__(*args, **kwargs)
        self._commit_on_exit = True
        self._is_committing = False

    async def commit(self) -> None:
        """Override commit to defer until final commit.

        This is the key method that makes our transaction management possible.
        Instead of committing immediately (like normal SQLAlchemy), we only
        allow commits when _is_committing is True (during final_commit).

        This means:
        1. All regular commit() calls in your code are intercepted
        2. Changes accumulate in the session
        3. Everything commits together at the end
        4. If anything fails, nothing is committed

        The clever part is that existing code continues to call commit()
        normally, but we silently defer those commits until the end.
        """
        if self._is_committing:
            await super().commit()

    async def final_commit(self) -> None:
        """Perform the actual commit operation.

        This is where the real database commit happens. We:
        1. Set _is_committing to True to allow the commit
        2. Perform the actual commit with all accumulated changes
        3. Reset _is_committing to False
        4. Handle any errors and ensure _is_committing is always reset
        """
        self._is_committing = True
        try:
            await super().commit()
        finally:
            self._is_committing = False

    async def rollback(self) -> None:
        """Rollback the session.

        Since we're just accumulating changes until the final commit,
        a rollback simply discards all pending changes.
        """
        await super().rollback()

    def set_commit_on_exit(self, value: bool) -> None:
        """Set whether to commit on exit.

        Args:
            value: If True, session will commit on exit
        """
        self._commit_on_exit = value


@asynccontextmanager
async def get_transactional_session(
    session_class: type[AsyncSession] = TxAsyncSession,
    commit_on_exit: bool = True,
) -> AsyncGenerator[TxAsyncSession, None]:
    """Get a transactional session.

    Usage:
        async with get_transactional_session() as session:
            # Do your database operations
            # All commits will be deferred until context exit
            await db_operation_1(session)
            await db_operation_2(session)
            # On context exit, all changes will be committed or rolled back

    Args:
        session_class: Session class to use
        commit_on_exit: Whether to commit on successful exit

    Yields:
        Transactional session
    """
    from app.db.db_session import async_sessionmaker

    async with async_sessionmaker() as session:
        if not isinstance(session, TxAsyncSession):
            session = TxAsyncSession(
                session.bind,
                **{k: v for k, v in session.__dict__.items() if not k.startswith("_")},
            )

        session.set_commit_on_exit(commit_on_exit)

        try:
            yield session
            if commit_on_exit:
                await session.final_commit()
        except Exception:
            await session.rollback()
            raise


def get_tx_session(
    commit_on_exit: bool = True,
) -> AsyncGenerator[TxAsyncSession, None]:
    """FastAPI dependency for getting a transactional session.

    Usage:
        @router.post("/")
        async def endpoint(session: TxAsyncSession = Depends(get_tx_session())):
            # Do your database operations
            # All commits will be deferred until endpoint completion
            await db_operation_1(session)
            await db_operation_2(session)
            # On successful completion, all changes will be committed

    Args:
        commit_on_exit: Whether to commit on successful exit

    Returns:
        Async generator yielding a transactional session
    """
    return get_transactional_session(commit_on_exit=commit_on_exit)
