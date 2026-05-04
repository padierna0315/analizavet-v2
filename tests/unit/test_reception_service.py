import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.reception import RawPatientInput, PatientSource, NormalizedPatient
from app.core.reception.service import ReceptionService
from app.models.patient import Patient
import json
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_receive_new_patient_creates_record():
    """Test that receiving a new patient creates a new record."""
    # Setup
    service = ReceptionService()
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mock the BaulService _find_existing to return None (no existing patient)
    # and register to return a new patient
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(service._baul, '_find_existing', AsyncMock(return_value=None))
        mp.setattr(service._baul, 'register', AsyncMock(return_value=MagicMock(
            patient_id=1,
            created=True,
            patient=NormalizedPatient(
                name="Firulais",
                species="Canino",
                sex="Macho",
                has_age=True,
                age_value=3,
                age_unit="años",
                age_display="3 años",
                owner_name="Juan Pérez",
                source=PatientSource.LIS_OZELLE
            )
        )))
        
        # Execute
        raw_input = RawPatientInput(
            raw_string="firulais canino 3a Juan Pérez",
            source=PatientSource.LIS_OZELLE,
            received_at=datetime.now(timezone.utc)
        )
        
        result = await service.receive(raw_input, mock_session)
        
        # Verify
        assert result.created is True
        assert result.patient_id == 1
        assert result.patient.name == "Firulais"


@pytest.mark.asyncio
async def test_receive_existing_patient_updates_demographic_data():
    """Test that receiving data for an existing patient updates demographic fields."""
    # Setup
    service = ReceptionService()
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Create an existing patient record (from Ozelle)
    existing_patient = Patient(
        id=1,
        name="Firulais",  # Original name from Ozelle
        species="Canino",
        sex="Macho",
        owner_name="Juan Pérez",  # Original owner from Ozelle
        has_age=True,
        age_value=3,
        age_unit="años",
        age_display="3 años",
        source=PatientSource.LIS_OZELLE.value,
        normalized_name="firulais",
        normalized_owner="juan perez",
        sources_received=[PatientSource.LIS_OZELLE.value]
    )
    
    # Mock the _find_existing method to return our existing patient
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(service._baul, '_find_existing', AsyncMock(return_value=existing_patient))
        mp.setattr(service._baul, 'register', AsyncMock())  # Should not be called
        
        # Execute - receive JSON data with different demographic info
        raw_input = RawPatientInput(
            raw_string="tommy canino 5a María García",  # Different name and owner
            source=PatientSource.MANUAL,  # JSON source treated as MANUAL for now
            received_at=datetime.now(timezone.utc)
        )
        
        result = await service.receive(raw_input, mock_session)
        
        # Verify
        assert result.created is False  # Should not create new patient
        assert result.patient_id == 1   # Should return existing patient ID
        
        # Verify the patient was updated with JSON data (demographic fields)
        assert existing_patient.name == "Tommy"  # Updated from JSON
        assert existing_patient.owner_name == "María García"  # Updated from JSON
        assert existing_patient.species == "Canino"  # Should remain same
        assert existing_patient.sex == "Macho"  # Should remain same
        assert existing_patient.has_age == True  # Should remain same
        assert existing_patient.age_value == 5  # Updated from JSON
        assert existing_patient.age_unit == "años"  # Should remain same
        assert existing_patient.age_display == "5 años"  # Updated from JSON
        
        # Verify sources_received was updated to include both sources
        sources_received = existing_patient.sources_received
        assert PatientSource.LIS_OZELLE.value in sources_received
        assert PatientSource.MANUAL.value in sources_received
        
        # Verify session was committed
        mock_session.commit.assert_awaited()
        mock_session.refresh.assert_awaited_with(existing_patient)


@pytest.mark.asyncio
async def test_receive_existing_patient_ozelle_data_preserved():
    """Test that Ozelle data is preserved when receiving JSON data later."""
    # Setup
    service = ReceptionService()
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Create an existing patient record (from Ozelle) with lab data association
    existing_patient = Patient(
        id=1,
        name="Firulais",
        species="Canino",
        sex="Macho",
        owner_name="Juan Pérez",
        has_age=True,
        age_value=3,
        age_unit="años",
        age_display="3 años",
        source=PatientSource.LIS_OZELLE.value,
        normalized_name="firulais",
        normalized_owner="juan perez",
        sources_received=[PatientSource.LIS_OZELLE.value]
    )
    
    # Mock the _find_existing method to return our existing patient
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(service._baul, '_find_existing', AsyncMock(return_value=existing_patient))
        mp.setattr(service._baul, 'register', AsyncMock())  # Should not be called
        
        # Execute - receive JSON data
        raw_input = RawPatientInput(
            raw_string="tommy canino 5a María García",
            source=PatientSource.MANUAL,  # JSON source
            received_at=datetime.now(timezone.utc)
        )
        
        result = await service.receive(raw_input, mock_session)
        
        # Verify Ozelle-related fields are preserved (though in this simplified model,
        # we don't have explicit lab data fields on Patient - that's in TestResult)
        # The key point is that we're not creating a new patient, so any existing
        # TestResult/Ozelle data would remain associated with this patient
        assert result.created is False
        assert result.patient_id == 1


@pytest.mark.asyncio
async def test_receive_same_source_twice_does_not_duplicate_sources():
    """Test that receiving data from the same source twice doesn't duplicate sources_received."""
    # Setup
    service = ReceptionService()
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Create an existing patient record
    existing_patient = Patient(
        id=1,
        name="Firulais",
        species="Canino",
        sex="Macho",
        owner_name="Juan Pérez",
        has_age=True,
        age_value=3,
        age_unit="años",
        age_display="3 años",
        source=PatientSource.LIS_OZELLE.value,
        normalized_name="firulais",
        normalized_owner="juan perez",
        sources_received=[PatientSource.LIS_OZELLE.value]
    )
    
    # Mock the _find_existing method to return our existing patient
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(service._baul, '_find_existing', AsyncMock(return_value=existing_patient))
        mp.setattr(service._baul, 'register', AsyncMock())  # Should not be called
        
        # Execute - receive Ozelle data twice
        raw_input = RawPatientInput(
            raw_string="firulais canino 3a Juan Pérez",
            source=PatientSource.LIS_OZELLE,
            received_at=datetime.now(timezone.utc)
        )
        
        result = await service.receive(raw_input, mock_session)
        
        # Verify
        assert result.created is False
        assert result.patient_id == 1
        
        # Verify sources_received still only contains one entry for LIS_OZELLE
        sources_received = existing_patient.sources_received
        assert sources_received.count(PatientSource.LIS_OZELLE.value) == 1
        assert len(sources_received) == 1