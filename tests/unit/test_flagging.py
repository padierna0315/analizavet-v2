import pytest
from app.core.taller.flagging import ClinicalFlaggingService

service = ClinicalFlaggingService()

def test_normal_value_canino():
    result = service.flag_value("RBC", 6.0, "x10^6/µL", "Canino")
    assert result.flag == "NORMAL"
    assert "4.95-7.87" in result.reference_range

def test_high_value_canino():
    result = service.flag_value("RBC", 8.0, "x10^6/µL", "Canino")
    assert result.flag == "ALTO"

def test_low_value_canino():
    result = service.flag_value("RBC", 4.0, "x10^6/µL", "Canino")
    assert result.flag == "BAJO"

def test_normal_value_felino():
    result = service.flag_value("RBC", 7.0, "x10^6/µL", "Felino")
    assert result.flag == "NORMAL"
    assert "5.0-10.0" in result.reference_range

def test_unknown_parameter_returns_normal():
    result = service.flag_value("UNKNOWN", 10.0, "units", "Canino")
    assert result.flag == "NORMAL"
    assert result.reference_range == ""

def test_unknown_species_raises():
    with pytest.raises(ValueError, match="Especie desconocida: Equino"):
        service.flag_value("RBC", 6.0, "x10^6/µL", "Equino")

def test_flag_batch():
    batch = [
        {"parameter": "RBC", "value": 6.0, "unit": "x10^6/µL"},
        {"parameter": "WBC", "value": 15.0, "unit": "x10^3/µL"}
    ]
    results = service.flag_batch(batch, "Canino")
    assert len(results) == 2
    assert results[0].flag == "NORMAL"