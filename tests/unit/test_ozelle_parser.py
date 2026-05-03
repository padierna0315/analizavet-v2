"""
Tests for app.satellites.ozelle.parser — Ozelle patient string parser
"""

import pytest
from app.satellites.ozelle.parser import OzelleReading, parse_ozelle_patient_string
from datetime import datetime


# ── Test data fixtures ─────────────────────────────────────────────────────────

TRADITIONAL_FORMAT = "kitty felina 2a Laura Cepeda"
"""Traditional name-first format"""

CODE_FIRST_SIMPLE = "A1 Ichigo"
"""Simple code-first format"""

CODE_FIRST_WITH_SPACES = "B12 Juan Perro"
"""Code-first with multi-word name"""

CODE_FIRST_TODAY = f"A1-20260501 Ichigo"  # Will be adjusted in test
"""Code-first with today's date expectation"""

EMPTY_STRING = ""
"""Empty input"""

WHITESPACE_ONLY = "   "
"""Whitespace-only input"""

INVALID_FORMAT_NO_SPACE = "A1Ichigo"
"""Missing space between code and name"""

INVALID_FORMAT_LOWERCASE = "a1 ichigo"
"""Lowercase code"""

INVALID_FORMAT_NO_LETTER = "1 ichigo"
"""Code doesn't start with letter"""


# ── OzelleReading dataclass tests ──────────────────────────────────────────────

class TestOzelleReading:
    def test_dataclass_fields(self):
        """Test OzelleReading dataclass fields."""
        reading = OzelleReading(
            session_code="A1-20260501",
            patient_name="Ichigo",
            full_patient_id="A1-20260501-Ichigo",
            raw_patient_string="A1 Ichigo"
        )
        assert reading.session_code == "A1-20260501"
        assert reading.patient_name == "Ichigo"
        assert reading.full_patient_id == "A1-20260501-Ichigo"
        assert reading.raw_patient_string == "A1 Ichigo"


# ── parse_ozelle_patient_string tests ──────────────────────────────────────────

class TestParseOzellePatientStringTraditional:
    """Tests for traditional name-first format (should return None)."""

    def test_traditional_format_returns_none(self):
        """Traditional format should return None (no session info)."""
        result = parse_ozelle_patient_string(TRADITIONAL_FORMAT)
        assert result is None

    def test_traditional_format_with_numbers_returns_none(self):
        """Traditional format with numbers should return None."""
        traditional_with_num = "POLO 5 años"
        result = parse_ozelle_patient_string(traditional_with_num)
        assert result is None


class TestParseOzellePatientStringCodeFirst:
    """Tests for code-first format."""

    def test_code_first_simple_parses_correctly(self):
        """Simple code-first format should parse correctly."""
        result = parse_ozelle_patient_string(CODE_FIRST_SIMPLE)
        assert result is not None
        assert result.session_code.startswith("A1-")  # Date part changes daily
        assert result.patient_name == "Ichigo"
        assert result.full_patient_id == f"{result.session_code}-Ichigo"
        assert result.raw_patient_string == CODE_FIRST_SIMPLE

    def test_code_first_with_spaces_in_name(self):
        """Code-first with multi-word patient name."""
        result = parse_ozelle_patient_string(CODE_FIRST_WITH_SPACES)
        assert result is not None
        assert result.session_code.startswith("B12-")
        assert result.patient_name == "Juan Perro"
        assert result.full_patient_id == f"{result.session_code}-Juan Perro"
        assert result.raw_patient_string == CODE_FIRST_WITH_SPACES

    def test_code_first_today_date(self):
        """Code-first should use today's date in session_code."""
        today_str = datetime.now().strftime('%Y%m%d')
        expected_session_prefix = f"A1-{today_str}"
        
        result = parse_ozelle_patient_string("A1 Isaac")
        assert result is not None
        assert result.session_code == expected_session_prefix
        assert result.patient_name == "Isaac"
        assert result.full_patient_id == f"{expected_session_prefix}-Isaac"
        assert result.raw_patient_string == "A1 Isaac"


class TestParseOzellePatientStringEdgeCases:
    """Edge case tests."""

    def test_empty_string_returns_none(self):
        """Empty input should return None."""
        result = parse_ozelle_patient_string(EMPTY_STRING)
        assert result is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only input should return None."""
        result = parse_ozelle_patient_string(WHITESPACE_ONLY)
        assert result is None

    def test_invalid_no_space_returns_none(self):
        """Missing space between code and name should return None."""
        result = parse_ozelle_patient_string(INVALID_FORMAT_NO_SPACE)
        assert result is None

    def test_invalid_lowercase_code_returns_none(self):
        """Lowercase code should return None."""
        result = parse_ozelle_patient_string(INVALID_FORMAT_LOWERCASE)
        assert result is None

    def test_invalid_no_leading_letter_returns_none(self):
        """Code not starting with letter should return None."""
        result = parse_ozelle_patient_string(INVALID_FORMAT_NO_LETTER)
        assert result is None

    def test_single_letter_with_digit_code_works(self):
        """Single letter with digit code (like A1) should work."""
        result = parse_ozelle_patient_string("A1 Paciente")
        assert result is not None
        assert result.session_code.startswith("A1-")
        assert result.patient_name == "Paciente"

    def test_multi_digit_code_works(self):
        """Multi-digit code (like B12) should work."""
        result = parse_ozelle_patient_string("B12 Paciente")
        assert result is not None
        assert result.session_code.startswith("B12-")
        assert result.patient_name == "Paciente"

    def test_code_with_letters_and_digits_only_letter_first(self):
        """Code must start with letter, but can have letters after? Actually spec says Letter+number."""
        # According to pattern [A-Z]\d+, it's letter followed by digits only
        result = parse_ozelle_patient_string("AB12 Paciente")  # This should fail as it's letter+letter+digits
        assert result is None  # Should not match our pattern

    def test_patient_name_can_have_hyphens(self):
        """Patient name can contain hyphens."""
        result = parse_ozelle_patient_string("A1 Perro-Lobo")
        assert result is not None
        assert result.session_code.startswith("A1-")
        assert result.patient_name == "Perro-Lobo"
        assert result.full_patient_id == f"{result.session_code}-Perro-Lobo"


class TestParseOzellePatientStringFaultTolerance:
    """Tests verifying fault tolerance requirements."""

    def test_none_input_returns_none(self):
        """None input should not crash, return None."""
        result = parse_ozelle_patient_string(None)
        assert result is None

    def test_non_string_input_returns_none(self):
        """Non-string input should not crash."""
        result = parse_ozelle_patient_string(12345)
        assert result is None

        result = parse_ozelle_patient_string(['A1', 'Ichigo'])
        assert result is None