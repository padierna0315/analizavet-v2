from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.schemas.reception import RawPatientInput, BaulResult
from app.core.reception.normalizer import parse_patient_string
from app.core.reception.baul import BaulService
from app.models.patient import Patient
import json
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

    async def get_waiting_room_patients(
        self, session: AsyncSession
    ) -> list[dict]:
        """Get all patients currently in the waiting room (sala de espera).
        
        Returns patients with waiting_room_status = 'active' formatted for display.
        """
        query = select(Patient).where(Patient.waiting_room_status == "active")
        query = query.order_by(Patient.updated_at.desc())
        
        result = await session.execute(query)
        patients = result.scalars().all()
        
        # Format patient data for the waiting room UI
        patients_data = []
        for patient in patients:
            # Parse sources_received JSON if it exists
            sources_received = []
            if patient.sources_received:
                try:
                    sources_received = json.loads(patient.sources_received)
                except (json.JSONDecodeError, TypeError):
                    sources_received = []
            
            patient_data = {
                "id": patient.id,
                "name": patient.name,
                "species": patient.species,
                "sex": patient.sex,
                "owner_name": patient.owner_name,
                "age_display": patient.age_display,
                "session_code": patient.session_code,
                "waiting_room_status": patient.waiting_room_status,
                "sources_received": sources_received,
                "created_at": patient.created_at.isoformat() if patient.created_at else None,
                "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
                # For backward compatibility with existing UI
                "source": patient.source,
                "normalized_name": patient.normalized_name,
                "normalized_owner": patient.normalized_owner
            }
            patients_data.append(patient_data)
        
        return patients_data
