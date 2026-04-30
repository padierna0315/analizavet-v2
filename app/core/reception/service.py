from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.reception import RawPatientInput, BaulResult
from app.core.reception.normalizer import parse_patient_string
from app.core.reception.baul import BaulService
import logfire


class ReceptionService:
    """Orchestrates the full reception flow:
    RawPatientInput → normalize → Baúl → BaulResult
    """

    def __init__(self):
        self._baul = BaulService()

    async def receive(
        self, raw_input: RawPatientInput, session: AsyncSession
    ) -> BaulResult:
        logfire.info(
            f"Recibiendo paciente: '{raw_input.raw_string}' "
            f"[fuente={raw_input.source.value}]"
        )
        normalized = parse_patient_string(raw_input.raw_string, raw_input.source)
        result = await self._baul.register(normalized, session)
        return result
