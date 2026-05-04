# Clinical Standards Specification

## Purpose

This spec defines the requirements for clinical standards in the taller module, ensuring all necessary parameters have appropriate reference ranges for Canine and Feline species.

## ADDED Requirements

### Requirement: Clinical Standards for Additional Parameters

The system MUST provide reference ranges for the following parameters for Canine and Feline species:
- `NSH#` — Neutrófilos Hipersegmentados
- `BAS#` — Basófilos  
- `HDW-CV`, `HDW-SD` — Ancho distribución hemoglobina
- `PDW` — Ancho distribución plaquetas
- `APLT#` — Plaquetas agregadas
- `P-LCC` — Concentración grandes plaquetas
- `LYM#` — verificar alias `LYM# → LYMP#` y resolver

#### Scenario: Clinical standards are applied to all specified parameters

- GIVEN a patient result with parameters `NSH#`, `BAS#`, `HDW-CV`, `HDW-SD`, `PDW`, `APLT#`, `P-LCC`, and `LYM#`
- WHEN the system processes these parameters
- THEN appropriate clinical standards are applied for Canine and Feline species

#### Scenario: LYM# parameter alias resolution

- GIVEN a parameter with code `LYM#`
- WHEN the system resolves parameter aliases
- THEN the system correctly maps `LYM#` to `LYMP#` if needed

## Verification Requirements

### Requirement: Post-fix Verification

After the fix, the system MUST meet these verification criteria:
- `GET /reports/{result_id}/pdf` returns a valid PDF (status 200, content-type application/pdf)
- The konsole does NOT show warnings of "Código de imagen desconocido" for the parameters of the standard hemogram
- The PDF button is visible when a patient is in the taller

#### Scenario: Successful PDF generation after fix

- GIVEN the fix is implemented
- WHEN a user requests a PDF report
- THEN the system generates a valid PDF without errors

#### Scenario: No warnings for hemogram parameters

- GIVEN an Ozelle instrument sends hemogram parameters
- WHEN the system processes these parameters
- THEN no warnings of "Código de imagen desconocido" are displayed for standard hemogram parameters