# Specification for Sala de Espera Persistent Feature

## Overview
This specification defines the requirements for implementing a persistent "Sala de Espera" feature that will keep patients visible in the reception interface until manually deleted or PDF generated.

## Patient Data Sources
The system handles data from multiple sources with specific requirements:

1. **Ozelle** (hemograma - 42+ parameters):
   - Traditional format: "Ichigo canino 5a Fernanda Hernandez..." (name-first)
   - NEW format: "A1 Ichigo..." (code-first, code ALWAYS comes first)

2. **Fujifilm** (química sanguínea): 
   - Implementation deferred to Stage 3

3. **JSON "La Recepcionista"**:
   - Format: "A1: Doctora Aura Betancourt, Paciente: Ichigo, tipo: canino, edad: 5 años, etc..."
   - Code ALWAYS first in all formats

## Code Format
- Codes include date: "A1-20260501", "G3-20260501" 
- Codes reset daily
- Full patient ID = code + date (e.g., "A1-20260501-Ichigo")

## Patient Merge Logic
- Ozelle data (hemograma) is SACRED and never changes
- JSON only updates: patient name, species, age, owner (not lab data)
- If Ozelle sends "A1 Ichigo" and JSON has "A1: ... Paciente: Tommy...", system must MERGE (keep Ozelle hemograma, update name to Tommy)
- Data from different sources can coexist in same DB (different types: patient info vs lab values)

## Source Check-ins (3 dots on patient card)
1. Dot 1 (top-left): Ozelle - green when hemograma data received
2. Dot 2 (top-center): Fujifilm - green when química sanguínea received  
3. Dot 3 (top-right): Recepcionista (JSON) - green when JSON baptizes patient

## UI Flow
- Patient arrives → appears in Reception grid as card
- If "A1 Ichigo" from Ozelle but no JSON yet → shows "A1 Ichigo" (temp name)
- When JSON uploaded → patient becomes "Tommy, Canino, 5 años, Dra. Aura Betancourt"
- Patient stays in grid until: manual deletion OR PDF generated

## Button "Subir Datos"
- REPLACES existing "Subir LIS" button
- Modal/dropdown asks: Ozelle? Fujifilm? .json?
- User selects, uploads, done

## Implementation Stages

### Stage 1: Planning, Documentation, Architecture
- Analyze complexity issues in current project
- Simplify and document existing code
- Prepare for new integrations
- Create clear architecture for data flow

### Stage 2: Ozelle Data Integrity
- Ensure Ozelle data flow works with:
  - Traditional parsing: "Ichigo canino 5a..." (already works)
  - NEW code-first parsing: "A1 Ichigo..." (code always first)
- Code-date format: "A1-20260501-Ichigo"
- Create/review tests for Ozelle pipeline

### Stage 3: Fujifilm Integration  
- Implement parser for Fujifilm data (from LIS port 6001 OR file upload)
- Integrate with waiting room check-ins

### Stage 4: Integration & Remaining Features
- Patient grid in Reception tab
- 3 check-in dots per patient card
- JSON upload and patient baptism
- Merge logic (Ozelle data + JSON patient info)
- PDF generation blocking when incomplete
- Manual deletion flow

## Data Model Changes

### Option A (Recommended): Extend Patient + TestResult
- Patient gets: `session_code` (e.g., "A1-20260501"), `waiting_room_status`, `sources_received` (JSON array)
- TestResult links to Patient, has `source` field

### Option B: New WaitingRoomEntry model
- Separate table tracking patient + sources + status

## UI Requirements
- Patient cards in GRID layout
- 3 circular dots per card (Ozelle/Fujifilm/JSON)
- Green = received, Gray = pending
- Patient shows temp name ("A1 Tommy") until JSON baptizes
- After JSON: full name, species, owner visible
- Card stays until user clicks trash icon OR generates PDF

## Key Technical Decisions
1. Use Patient.session_code + Patient.session_date for daily code management
2. Sources stored as JSON array in Patient model
3. Merge = JSON updates Patient fields, TestResult stays with Ozelle data
4. PDF blocked if: no JSON OR no lab data from at least one machine