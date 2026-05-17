# Reception Fallback Matching Specification

## Purpose

When lab results arrive without a `session_code`, the fallback matching by
normalized name MUST verify uniqueness before reusing a patient record. This
prevents cross-contamination when multiple patients share the same name. This
spec governs the Fujifilm, Ozelle, and File source paths in reception.

## Requirements

### Requirement: Fallback name-matching MUST be unique

When matching by `normalized_name` in the absence of a `session_code` match,
the system MUST select an existing patient ONLY when exactly one patient
shares that normalized name. If zero or two or more patients share the name,
the system MUST create a new patient record.

#### Scenario: Exactly one match

- GIVEN exactly one patient exists with `normalized_name = "KIARA"`
- WHEN a Fujifilm result arrives with `raw_string = "KIARA"` and no `session_code`
- THEN the system reuses the existing patient
- AND returns `BaulResult(created=False)`

#### Scenario: Multiple matches

- GIVEN two patients exist with `normalized_name = "KIARA"`
- WHEN a Fujifilm result arrives with `raw_string = "KIARA"` and no `session_code`
- THEN the system creates a new patient record
- AND returns `BaulResult(created=True)`

#### Scenario: No match

- GIVEN no patient exists with `normalized_name = "KIARA"`
- WHEN a Fujifilm result arrives with `raw_string = "KIARA"` and no `session_code`
- THEN the system creates a new patient record
- AND returns `BaulResult(created=True)`

### Requirement: `session_code` matching takes priority

The system MUST attempt `session_code`-based matching before any fallback
name-matching. Fallback by name applies ONLY when `session_code` is absent
or does not match any patient.

#### Scenario: Session_code present, match found

- GIVEN a patient exists with `session_code = "M5"` and `normalized_name = "KIARA"`
- WHEN a Fujifilm result arrives with `session_code = "M5"`
- THEN the system matches by `session_code`, not by name
- AND returns `BaulResult(created=False)`

### Requirement: `raw_string` MUST NOT serve as lookup code

The system MUST NOT use `raw_input.raw_string` as a session_code lookup.
The `session_code` field is the sole authority for code-based patient
matching.

#### Scenario: No session_code, raw_string present

- GIVEN a patient with `session_code = "M5"` exists
- WHEN a result arrives with empty `session_code` and `raw_string = "M5"`
- THEN the system does NOT match by `raw_string`
- AND proceeds to name-based fallback matching
