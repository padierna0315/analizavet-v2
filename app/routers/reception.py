from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.database import get_session
from app.schemas.reception import RawPatientInput, BaulResult, NormalizedPatient
from app.models.patient import Patient
from app.core.reception.service import ReceptionService
from loguru import logger

router = APIRouter(prefix="/reception", tags=["Recepción"])
_service = ReceptionService()


@router.post("/receive", response_model=BaulResult)
async def receive_patient(
    body: RawPatientInput,
    session: AsyncSession = Depends(get_session),
):
    """Receive a raw patient string, normalize it, and register in the Baúl.
    
    Returns the patient ID and whether it was newly created.
    
    Example body:
    {
        "raw_string": "kitty felina 2a Laura Cepeda",
        "source": "LIS_OZELLE",
        "received_at": "2026-04-24T10:00:00Z"
    }
    """
    try:
        return await _service.receive(body, session)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/patients", response_model=dict)
async def list_patients(
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    species: str | None = Query(default=None, description="Filtrar por especie: Canino o Felino"),
    owner: str | None = Query(default=None, description="Filtrar por nombre del tutor"),
):
    """List all registered patients with pagination and optional filters."""
    query = select(Patient)
    
    if species:
        query = query.where(Patient.species == species)
    if owner:
        query = query.where(Patient.owner_name.icontains(owner))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Patient.updated_at.desc())
    result = await session.execute(query)
    patients = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "patients": [
            {
                "id": p.id,
                "name": p.name,
                "species": p.species,
                "sex": p.sex,
                "age_display": p.age_display,
                "owner_name": p.owner_name,
                "source": p.source,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in patients
        ],
    }


@router.get("/patients/{patient_id}", response_model=dict)
async def get_patient(
    patient_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get full detail of a single patient by ID."""
    result = await session.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalars().first()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Paciente con ID {patient_id} no encontrado"
        )
    
    return {
        "id": patient.id,
        "name": patient.name,
        "species": patient.species,
        "sex": patient.sex,
        "has_age": patient.has_age,
        "age_value": patient.age_value,
        "age_unit": patient.age_unit,
        "age_display": patient.age_display,
        "owner_name": patient.owner_name,
        "source": patient.source,
        "created_at": patient.created_at.isoformat(),
        "updated_at": patient.updated_at.isoformat(),
    }
