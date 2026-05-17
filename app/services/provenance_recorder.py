"""ProvenanceRecorder — capture facade for raw data provenance.

All methods wrap database operations in try/except so that a capture
or linking failure never propagates to the main pipeline.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.raw_data_log import RawDataLog, RawDataSource

logger = logging.getLogger(__name__)


class ProvenanceRecorder:
    """Single entry point for recording raw data provenance.

    Two capture modes:
    - record_sync(): synchronous, reuses caller's session (AppSheet).
    - record_async(): synchronous write, returns record ID (Ozelle/Fujifilm).
      Will be refactored to Dramatiq fire-and-forget in PR 2.
    """

    @staticmethod
    async def record_sync(
        session: AsyncSession,
        source: RawDataSource,
        raw_data: str,
        received_at: datetime,
        *,
        session_code: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> None:
        """Capture raw data synchronously using the caller's DB session.

        Used by AppSheet — the session is shared with the main processing
        flow so that capture and processing share the same transaction.
        """
        try:
            log = RawDataLog(
                source=source.value,
                raw_data=raw_data,
                received_at=received_at,
                session_code=session_code,
                raw_metadata=metadata,
            )
            session.add(log)
            await session.flush()
        except Exception:
            logger.exception(
                "ProvenanceRecorder.record_sync failed (source=%s, session_code=%s)",
                source.value,
                session_code,
            )

    @staticmethod
    async def record_async(
        session: AsyncSession,
        source: RawDataSource,
        raw_data: str,
        received_at: datetime,
        *,
        session_code: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> Optional[int]:
        """Capture raw data and return the new record ID.

        Used by Ozelle and Fujifilm. In PR 1 this is a direct DB write.
        In PR 2 it will be refactored to fire-and-forget via Dramatiq.

        Returns the RawDataLog.id on success, None on failure.
        """
        try:
            log = RawDataLog(
                source=source.value,
                raw_data=raw_data,
                received_at=received_at,
                session_code=session_code,
                raw_metadata=metadata,
            )
            session.add(log)
            await session.flush()
            await session.refresh(log)
            return log.id
        except Exception:
            logger.exception(
                "ProvenanceRecorder.record_async failed (source=%s, session_code=%s)",
                source.value,
                session_code,
            )
            return None

    @staticmethod
    async def link_to_patient(
        session: AsyncSession,
        session_code: str,
        patient_id: int,
        *,
        test_result_id: Optional[int] = None,
    ) -> None:
        """Backfill patient_id and test_result_id on matching RawDataLog rows.

        Updates ALL rows with the given session_code. Sets status='linked'
        and records processed_at timestamp.
        """
        try:
            stmt = (
                update(RawDataLog)
                .where(RawDataLog.session_code == session_code)  # type: ignore[arg-type]
                .values(
                    patient_id=patient_id,
                    test_result_id=test_result_id,
                    status="linked",
                    processed_at=datetime.now(timezone.utc),
                )
            )
            await session.execute(stmt)
        except Exception:
            logger.exception(
                "ProvenanceRecorder.link_to_patient failed "
                "(session_code=%s, patient_id=%d)",
                session_code,
                patient_id,
            )
