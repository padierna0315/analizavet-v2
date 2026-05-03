from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List
import json
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSON as SQLModelJSON

if TYPE_CHECKING:
    from app.models.test_result import TestResult


class Patient(SQLModel, table=True):
    """The Baúl — every patient registered in the system.
    
    Deduplication key: normalized_name + normalized_owner + species
    (stored as lowercase, accent-stripped for comparison)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Display fields (naturalized, capitalized)
    name: str                   # "Kitty"
    species: str                # "Canino" or "Felino"
    sex: str                    # "Macho" or "Hembra"
    owner_name: str             # "Laura Cepeda"
    
    # Age fields (None for coproscopics)
    has_age: bool = Field(default=True)
    age_value: Optional[int] = Field(default=None)
    age_unit: Optional[str] = Field(default=None)   # "años" or "meses"
    age_display: Optional[str] = Field(default=None) # "2 años"
    
    # Source tracking
    source: str                 # PatientSource value as string
    
    # Waiting room fields (for sala-espera-persistente)
    session_code: Optional[str] = Field(default=None, index=True)  # e.g., "A1-20260501"
    waiting_room_status: str = Field(default="active")  # active, deleted, pdf_generated
    sources_received: Optional[List[str]] = Field(default=None, sa_column=Column(SQLModelJSON))  # Track which sources have provided data (Ozelle, Fujifilm, JSON)
    
    # Deduplication keys (normalized: lowercase + no accents)
    # These are used for comparison only — never displayed
    normalized_name: str = Field(index=True)
    normalized_owner: str = Field(index=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    test_results: list["TestResult"] = Relationship(back_populates="patient")
