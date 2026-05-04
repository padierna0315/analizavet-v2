from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
import logfire

from app.shared.models.test_result import TestResult
from app.shared.models.lab_value import LabValue
from app.shared.models.patient_image import PatientImage
from app.domains.patients.models import Patient
from app.domains.taller.schemas import (
    FlagBatchRequest, FlagBatchResult,
    ImageUploadRequest, ImageUploadResult,
    RawLabValueInput,
)
from app.domains.taller.engine import TallerFlaggingEngine
from app.domains.taller.images import ImageHandlingService


class TallerService:
    """Orchestrates the Taller: flagging + image handling."""

    def __init__(self):
        self._engine = TallerFlaggingEngine()
        self._images = ImageHandlingService()

    async def create_test_result(
        self,
        patient_id: int,
        test_type: str,
        test_type_code: str,
        source: str,
        received_at: datetime,
        session: AsyncSession,
    ) -> TestResult:
        """Create a new TestResult record for a patient."""
        tr = TestResult(
            patient_id=patient_id,
            test_type=test_type,
            test_type_code=test_type_code,
            source=source,
            status="pendiente",
            received_at=received_at,
        )
        session.add(tr)
        await session.commit()
        await session.refresh(tr)
        logfire.info(f"TestResult creado: id={tr.id} patient={patient_id} tipo={test_type}")
        return tr

    async def flag_and_store(
        self,
        test_result_id: int,
        species: str,
        values: list[RawLabValueInput],
        session: AsyncSession,
    ) -> FlagBatchResult:
        """Flag all lab values and store in DB."""
        request = FlagBatchRequest(
            test_result_id=test_result_id,
            species=species,
            values=values,
        )
        return await self._engine.flag_test_result(request, session)

    async def save_images(
        self,
        request: ImageUploadRequest,
        session: AsyncSession,
    ) -> ImageUploadResult:
        return await self._images.save_images(request, session)

    async def get_test_result_full(
        self,
        test_result_id: int,
        session: AsyncSession,
    ) -> dict | None:
        """Get TestResult with all LabValues, images, and patient info.

        Usa una sola consulta con eager loading (Tubería Maestra) para evitar
        el problema N+1. La regla de "Estricto con el paciente" garantiza
        que solo traemos resultados que tengan paciente asociado.
        """
        # Una sola consulta que trae TODO: TestResult + Patient + LabValues + Images
        result = await session.execute(
            select(TestResult)
            .where(TestResult.id == test_result_id)
            .join(Patient)  # Regla: estricto con el paciente
            .options(
                selectinload(TestResult.patient),
                selectinload(TestResult.lab_values),
                selectinload(TestResult.images),
            )
        )
        tr = result.scalars().first()
        if not tr:
            return None

        # Los datos ya vienen precargados gracias a selectinload
        patient = tr.patient
        lab_values = tr.lab_values
        images = tr.images

        return {
            "test_result": {
                "id": tr.id,
                "patient_id": tr.patient_id,
                "test_type": tr.test_type,
                "test_type_code": tr.test_type_code,
                "source": tr.source,
                "status": tr.status,
                "flag_alto_count": tr.flag_alto_count,
                "flag_normal_count": tr.flag_normal_count,
                "flag_bajo_count": tr.flag_bajo_count,
                "received_at": tr.received_at.isoformat(),
                "processed_at": tr.processed_at.isoformat() if tr.processed_at else None,
            },
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "species": patient.species,
                "sex": patient.sex,
                "age_display": patient.age_display,
                "owner_name": patient.owner_name,
            } if patient else None,
            "lab_values": [
                {
                    "id": lv.id,
                    "parameter_code": lv.parameter_code,
                    "parameter_name_es": lv.parameter_name_es,
                    "raw_value": lv.raw_value,
                    "numeric_value": lv.numeric_value,
                    "unit": lv.unit,
                    "reference_range": lv.reference_range,
                    "flag": lv.flag,
                    "machine_flag": lv.machine_flag,
                }
                for lv in lab_values
            ],
            "images": [
                {
                    "id": img.id,
                    "obs_identifier": img.parameter_code,
                    "parameter_name_es": img.parameter_name_es,
                    "image_type": img.image_type,
                    "file_path": img.file_path,
                    "is_included_in_report": img.is_included_in_report,
                }
                for img in images
            ],
            "summary": {
                "ALTO": tr.flag_alto_count,
                "NORMAL": tr.flag_normal_count,
                "BAJO": tr.flag_bajo_count,
            },
        }