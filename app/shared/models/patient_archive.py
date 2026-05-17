from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class PatientArchive(SQLModel, table=True):
    """Permanent snapshot of a retired patient's data.

    Created when a patient's PDF is downloaded. Stores the full data dict
    from TallerService.get_test_result_full() as a JSON string so PDFs can
    be regenerated without the original database rows.

    Table name uses lowercase for SQL compatibility.
    """

    __tablename__ = "patientarchive"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Searchable identifiers
    session_code: Optional[str] = Field(default=None, index=True)
    patient_name: str
    owner_name: str
    species: str

    # When the patient was archived (retired)
    archived_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Full JSON snapshot — same format as TallerService.get_test_result_full() return
    snapshot_data: str  # JSON string

    # Back-reference to the original records (for traceability)
    original_patient_id: Optional[int] = Field(default=None)
    original_test_result_id: Optional[int] = Field(default=None)
