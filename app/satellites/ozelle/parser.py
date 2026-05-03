#!/usr/bin/env python3

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class OzelleReading:
    """Structured representation of parsed Ozelle patient data."""
    session_code: str  # e.g. "A1-20260501"
    patient_name: str  # e.g. "Ichigo"
    full_patient_id: str  # e.g. "A1-20260501-Ichigo"
    raw_patient_string: str  # Original string from PID[9]


def parse_ozelle_patient_string(raw_string: str) -> Optional[OzelleReading]:
    """
    Parse Ozelle patient string supporting both formats:
    1. Traditional: "kitty felina 2a Laura Cepeda" (name-first)
    2. Code-first: "A1 Ichigo..." (code always first)
    
    For code-first format, extracts:
    - Session code: code + today's date (e.g., "A1-20260501")
    - Patient name: the name part after the code
    - Full patient ID: session_code + "-" + patient_name
    
    For traditional format, returns None as it doesn't contain session info.
    
    Args:
        raw_string: Raw patient string from PID[9] (e.g., "A1 Ichigo" or "kitty felina 2a Laura Cepeda")
        
    Returns:
        OzelleReading if code-first format detected, None for traditional format
    """
    try:
        if not raw_string or not isinstance(raw_string, str):
            logger.debug(f"parse_ozelle_patient_string: invalid input type={type(raw_string)}")
            return None
            
        # Strip whitespace
        raw_string = raw_string.strip()
        
        if not raw_string:
            return None
            
        # Check if it matches code-first pattern: CODE SPACE NAME...
        # Code pattern: Letter + number (e.g., A1, G3, B12)
        # Name pattern: starts with letter, can contain letters, spaces, hyphens
        code_first_pattern = r'^([A-Z]\d+)\s+(.+)$'
        match = re.match(code_first_pattern, raw_string)
        
        if match:
            code = match.group(1)  # e.g., "A1"
            patient_name = match.group(2).strip()  # e.g., "Ichigo"
            
            # Validate patient name is not empty
            if not patient_name:
                logger.debug(f"parse_ozelle_patient_string: empty patient name after code '{code}'")
                return None
                
            # Generate session code using today's date
            today = datetime.now()
            session_code = f"{code}-{today.strftime('%Y%m%d')}"  # e.g., "A1-20260501"
            
            # Generate full patient ID
            full_patient_id = f"{session_code}-{patient_name}"  # e.g., "A1-20260501-Ichigo"
            
            reading = OzelleReading(
                session_code=session_code,
                patient_name=patient_name,
                full_patient_id=full_patient_id,
                raw_patient_string=raw_string
            )
            
            logger.debug(f"parse_ozelle_patient_string: parsed code-first format: {reading}")
            return reading
        else:
            # Traditional format (name-first) - no session code info
            logger.debug(f"parse_ozelle_patient_string: traditional format detected: '{raw_string}'")
            return None
            
    except Exception as e:
        logger.error(f"parse_ozelle_patient_string: unexpected error: {e}", exc_info=True)
        return None