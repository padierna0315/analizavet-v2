"""RawDataLog — immutable audit trail of every raw message received.

One row = one incoming payload captured BEFORE parsing.
All foreign keys are nullable and use ON DELETE SET NULL so that
retiring a patient or test result never cascades into this audit table.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlmodel import Field, SQLModel


class RawDataSource(str, Enum):
    """Discriminator for which external system sent the raw data."""

    APPSHEET = "appsheet"
    OZELLE = "ozelle"
    FUJIFILM = "fujifilm"


class RawDataStatus(str, Enum):
    """Lifecycle state of a raw data record."""

    PENDING = "pending"
    LINKED = "linked"
    ARCHIVED = "archived"


class RawDataLog(SQLModel, table=True):
    """One raw incoming payload — captured BEFORE parsing.

    This is the system's "black box" recorder. Every message from
    AppSheet, Ozelle, or Fujifilm is written here before any processing
    happens, preserving the original bytes for audit and debugging.
    """

    __tablename__ = "rawdatalog"

    id: Optional[int] = Field(default=None, primary_key=True)

    source: str  # "appsheet" | "ozelle" | "fujifilm"

    raw_data: str  # Full payload — JSON, HL7, or TCP plain text (TEXT column)

    received_at: datetime  # When the external system sent it

    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    processed_at: Optional[datetime] = Field(default=None)

    patient_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("patient.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
    )

    test_result_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("testresult.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
    )

    session_code: Optional[str] = Field(default=None, index=True)

    status: str = Field(default="pending")

    error_message: Optional[str] = Field(default=None)

    raw_metadata: Optional[str] = Field(
        default=None,
        sa_column=Column("metadata", Text, nullable=True),
    )
