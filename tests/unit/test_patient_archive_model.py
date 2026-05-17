"""Tests for PatientArchive SQLModel — creation, JSON serialization, DB roundtrip."""

import json
from datetime import datetime, timezone

import pytest
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest_asyncio

from app.shared.models.patient_archive import PatientArchive
from app.domains.patients.models import Patient


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    await engine.dispose()


# ── Model creation (no DB) ───────────────────────────────────────────────


class TestPatientArchiveCreation:
    """Pure model instantiation — no database needed."""

    def test_create_with_required_fields(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
        )
        assert archive.patient_name == "Kitty"
        assert archive.owner_name == "Laura Cepeda"
        assert archive.species == "Felino"

    def test_default_id_is_none(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
        )
        assert archive.id is None

    def test_default_session_code_is_none(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
        )
        assert archive.session_code is None

    def test_default_original_ids_are_none(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
        )
        assert archive.original_patient_id is None
        assert archive.original_test_result_id is None

    def test_archived_at_is_set_on_creation(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
        )
        assert isinstance(archive.archived_at, datetime)

    def test_session_code_can_be_set(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            session_code="A1-20260501",
        )
        assert archive.session_code == "A1-20260501"

    def test_original_patient_id_can_be_set(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            original_patient_id=42,
        )
        assert archive.original_patient_id == 42

    def test_original_test_result_id_can_be_set(self):
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            original_test_result_id=99,
        )
        assert archive.original_test_result_id == 99


# ── JSON snapshot serialization ──────────────────────────────────────────


class TestPatientArchiveSnapshot:
    """JSON snapshot roundtrip — simulates get_test_result_full() output format."""

    def _make_snapshot_dict(self) -> dict:
        """Return a dict matching TallerService.get_test_result_full() output format."""
        return {
            "test_result": {
                "id": 1,
                "patient_id": 5,
                "test_type": "Química Sanguínea",
                "test_type_code": "CHEM",
                "source": "LIS_FUJIFILM",
                "status": "pendiente",
                "flag_alto_count": 2,
                "flag_normal_count": 3,
                "flag_bajo_count": 1,
                "received_at": "2026-05-01T10:00:00",
                "processed_at": None,
                "doctor_name": "Dr. García",
                "copro_color": None,
                "copro_consistencia": None,
                "copro_olor": None,
                "copro_moco": None,
                "cito_color": None,
                "cito_turbidez": None,
                "cito_aspecto": None,
            },
            "patient": {
                "id": 5,
                "name": "Kitty",
                "species": "Felino",
                "sex": "Hembra",
                "age_display": "2 años",
                "owner_name": "Laura Cepeda",
                "breed": "Siamés",
                "doctor_name": "Dr. García",
            },
            "lab_values": [
                {
                    "id": 10,
                    "parameter_code": "CRE",
                    "parameter_name_es": "Creatinina",
                    "raw_value": "1.2",
                    "numeric_value": 1.2,
                    "unit": "mg/dL",
                    "reference_range": "0.8-1.8",
                    "flag": "NORMAL",
                    "machine_flag": "N",
                    "group": "RENAL",
                },
                {
                    "id": 11,
                    "parameter_code": "BUN",
                    "parameter_name_es": "Nitrógeno Ureico",
                    "raw_value": "25.0",
                    "numeric_value": 25.0,
                    "unit": "mg/dL",
                    "reference_range": "7-27",
                    "flag": "NORMAL",
                    "machine_flag": "N",
                    "group": "RENAL",
                },
                {
                    "id": 12,
                    "parameter_code": "ALT",
                    "parameter_name_es": "Alanina Aminotransferasa",
                    "raw_value": "150.0",
                    "numeric_value": 150.0,
                    "unit": "U/L",
                    "reference_range": "10-100",
                    "flag": "ALTO",
                    "machine_flag": "H",
                    "group": "HEPÁTICO",
                },
            ],
            "images": [
                {
                    "id": 1,
                    "obs_identifier": "WBC",
                    "parameter_name_es": "Leucocitos",
                    "image_type": "histogram",
                    "file_path": "images/Kitty_LauraCepeda/20260501/Leucocitos.png",
                    "is_included_in_report": True,
                },
            ],
            "summary": {"ALTO": 1, "NORMAL": 2, "BAJO": 0},
            "interpretations": [
                {
                    "parameter_code": "ALT",
                    "parameter_name_es": "Alanina Aminotransferasa",
                    "flag": "ALTO",
                    "text_es": "ALT elevado sugiere daño hepatocelular.",
                    "severity": "Moderado",
                }
            ],
            "exam_orders": [
                {
                    "id": 1,
                    "session_code": "A1-20260501",
                    "exam_types": ["CHEM_BASIC"],
                    "status": "pending",
                    "created_at": "2026-05-01T09:00:00",
                }
            ],
        }

    def test_snapshot_serialization_preserves_all_keys(self):
        """JSON roundtrip preserves all top-level keys from get_test_result_full()."""
        snapshot = self._make_snapshot_dict()
        json_str = json.dumps(snapshot)
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            snapshot_data=json_str,
        )

        # Deserialize and verify all top-level keys
        loaded = json.loads(archive.snapshot_data)
        expected_keys = {
            "test_result", "patient", "lab_values", "images",
            "summary", "interpretations", "exam_orders",
        }
        assert set(loaded.keys()) == expected_keys

    def test_snapshot_preserves_nested_values(self):
        """Nested values survive the JSON roundtrip unchanged."""
        snapshot = self._make_snapshot_dict()
        json_str = json.dumps(snapshot)
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            snapshot_data=json_str,
        )

        loaded = json.loads(archive.snapshot_data)
        assert loaded["test_result"]["test_type"] == "Química Sanguínea"
        assert loaded["patient"]["name"] == "Kitty"
        assert len(loaded["lab_values"]) == 3
        assert loaded["lab_values"][0]["parameter_code"] == "CRE"
        assert loaded["summary"]["ALTO"] == 1

    def test_snapshot_preserves_numeric_types(self):
        """Numeric values (int/float) survive the JSON roundtrip."""
        snapshot = self._make_snapshot_dict()
        json_str = json.dumps(snapshot)
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            snapshot_data=json_str,
        )

        loaded = json.loads(archive.snapshot_data)
        lv = loaded["lab_values"][0]
        assert isinstance(lv["numeric_value"], (int, float))
        assert lv["numeric_value"] == 1.2
        assert isinstance(lv["id"], int)
        assert isinstance(loaded["summary"]["ALTO"], int)

    def test_empty_arrays_preserved(self):
        """Empty arrays in snapshot survive the roundtrip."""
        snapshot = {
            "test_result": {"id": 1, "patient_id": 5},
            "patient": {"name": "Test"},
            "lab_values": [],
            "images": [],
            "summary": {},
            "interpretations": [],
            "exam_orders": [],
        }
        json_str = json.dumps(snapshot)
        archive = PatientArchive(
            patient_name="Test",
            owner_name="Owner",
            species="Canino",
            snapshot_data=json_str,
        )

        loaded = json.loads(archive.snapshot_data)
        assert loaded["lab_values"] == []
        assert loaded["images"] == []
        assert loaded["exam_orders"] == []


# ── Database integration ─────────────────────────────────────────────────


@pytest.mark.asyncio
class TestPatientArchiveDB:
    """Database round-trip tests."""

    async def test_create_and_retrieve(self, session: AsyncSession):
        snapshot = json.dumps({"patient": {"name": "Kitty"}, "lab_values": []})
        archive = PatientArchive(
            patient_name="Kitty",
            owner_name="Laura Cepeda",
            species="Felino",
            session_code="A1-20260501",
            snapshot_data=snapshot,
            original_patient_id=5,
            original_test_result_id=10,
        )
        session.add(archive)
        await session.commit()
        await session.refresh(archive)

        assert archive.id is not None
        assert archive.patient_name == "Kitty"
        assert archive.owner_name == "Laura Cepeda"
        assert archive.species == "Felino"
        assert archive.session_code == "A1-20260501"
        assert archive.original_patient_id == 5
        assert archive.original_test_result_id == 10
        assert isinstance(archive.archived_at, datetime)

        # Verify snapshot roundtrip from DB
        loaded = json.loads(archive.snapshot_data)
        assert loaded["patient"]["name"] == "Kitty"

    async def test_session_code_indexed(self, session: AsyncSession):
        """Verify session_code is stored and queryable."""
        archive = PatientArchive(
            patient_name="Doggy",
            owner_name="Owner",
            species="Canino",
            session_code="B2-20260502",
            snapshot_data=json.dumps({"test_result": {"id": 1}}),
        )
        session.add(archive)
        await session.commit()

        from sqlmodel import select
        stmt = select(PatientArchive).where(PatientArchive.session_code == "B2-20260502")
        result = await session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.patient_name == "Doggy"

    async def test_multiple_archives(self, session: AsyncSession):
        """Multiple archives can coexist."""
        a1 = PatientArchive(
            patient_name="P1", owner_name="O1", species="Canino",
            snapshot_data=json.dumps({"test_result": {"id": 1}}),
        )
        a2 = PatientArchive(
            patient_name="P2", owner_name="O2", species="Felino",
            snapshot_data=json.dumps({"test_result": {"id": 2}}),
        )
        session.add_all([a1, a2])
        await session.commit()

        assert a1.id is not None
        assert a2.id is not None
        assert a1.id != a2.id
