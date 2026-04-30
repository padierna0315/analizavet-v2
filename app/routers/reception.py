from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.database import get_session
from app.schemas.reception import RawPatientInput, BaulResult, NormalizedPatient
from app.models.patient import Patient
from app.models.test_result import TestResult
from app.core.reception.service import ReceptionService
from loguru import logger
import uuid

# Import Dramatiq actor for batch processing
from app.tasks.hl7_processor import process_uploaded_batch

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

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


@router.post("/upload")
async def upload_hl1_batch(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Handle HL7 batch file upload and process it."""
    try:
        # Read the file content
        content = await file.read()
        
        # Convert bytes to string for JSON serialization (Dramatiq)
        content_str = content.decode('utf-8')
        
        # Validate not empty
        if not content_str.strip():
            raise HTTPException(status_code=422, detail="HL7 file is empty")
        
        # Validate contains MSH segment (basic HL7 format check)
        if "MSH|" not in content_str:
            raise HTTPException(status_code=422, detail="Invalid HL7 format: missing MSH segment")
        
        # Send the file content to the Dramatiq actor for processing
        process_uploaded_batch.send(content_str)
        
        logger.info(f"Received HL7 batch file: {file.filename}")
        return RedirectResponse(url="/taller/", status_code=303)
    except HTTPException:
        raise  # re-raise HTTPException as is
    except Exception as e:
        logger.error(f"Error processing HL7 batch file: {e}")
        raise HTTPException(status_code=500, detail="Error processing HL7 file")


@router.post("/reception/procesar/{test_result_id}")
async def process_test_result(
    test_result_id: int,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
):
    """Process a test result and move it to the taller."""
    # Get the test result by ID
    statement = select(TestResult).where(TestResult.id == test_result_id)
    result = await session.execute(statement)
    test_result = result.scalar_one_or_none()
    
    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    # Update the status to "pendiente"
    test_result.status = "pendiente"
    session.add(test_result)
    await session.commit()
    
    # Return HTML for HTMX to update the row
    if request:
        return templates.TemplateResponse("recepcion/patient_processed.html", {
            "request": request,
            "test_result": test_result
        })
    else:
        return {"status": "success", "message": "Test result moved to taller"}


@router.get("/recepcion")
async def get_recepcion(request: Request, session: AsyncSession = Depends(get_session)):
    """Display the queue of patients with status="recibido"."""
    # Query for test results with status="recibido" and join with patient data
    query = select(TestResult, Patient).join(Patient).where(TestResult.status == "recibido")
    result = await session.execute(query)
    results = result.all()
    
    # Group test results by patient for display
    patients_data = {}
    for test_result, patient in results:
        if patient.id not in patients_data:
            patients_data[patient.id] = {
                "patient": patient,
                "test_results": []
            }
        patients_data[patient.id]["test_results"].append(test_result)
    
    # Convert to list for template rendering
    patients_list = list(patients_data.values())
    
    return templates.TemplateResponse("recepcion/index.html", {
        "request": request,
        "patients": patients_list
    })



