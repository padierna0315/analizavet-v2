# Patient Archive Specification

## Purpose

Define the permanent retirement flow: snapshot patient data on PDF download success, cascade-delete from main tables, and enable PDF regeneration from archived snapshots.

## Requirements

### Requirement: PatientArchive Table Schema

The system MUST store a `PatientArchive` table with a JSON blob column for denormalized snapshot data.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK, auto | Primary key |
| `session_code` | String, indexed | Original session_code for lookup |
| `patient_name` | String | Denormalized for quick display |
| `owner_name` | String | Denormalized for quick display |
| `species` | String | Denormalized for quick display |
| `archived_at` | DateTime, UTC | When the archive was created |
| `snapshot_data` | JSON/Text | Full denormalized blob (see below) |
| `original_patient_id` | Integer, nullable | Original patient ID before deletion |
| `original_test_result_id` | Integer, nullable | Original test_result ID before deletion |

The `snapshot_data` JSON blob MUST contain:
- `patient`: Full Patient fields (all columns from Patient table)
- `test_result`: Full TestResult fields
- `lab_values`: Array of LabValue objects (all columns)
- `images`: Array of PatientImage objects (all columns)
- `exam_orders`: Array of ExamOrder objects (all columns)

#### Scenario: Store complete snapshot on retirement

- GIVEN a patient with 1 TestResult, 3 LabValues, 2 PatientImages, and 1 ExamOrder
- WHEN the retirement flow executes
- THEN a single `PatientArchive` row is created
- AND the `snapshot_data` JSON contains all 5 entities with correct field values

#### Scenario: Archive columns match source model fields

- GIVEN an archived patient
- WHEN the snapshot is read back
- THEN every field from Patient, TestResult, LabValue, PatientImage, and ExamOrder is preserved
- AND numeric, string, datetime, and boolean types are correctly serialized/deserialized

### Requirement: Atomic Retirement on PDF Download

The system MUST execute retirement as a two-phase atomic operation: snapshot THEN delete.

Phase 1 — Archive:
1. Verify patient has at least one TestResult with lab data
2. Serialize Patient + all FK-related rows to JSON
3. INSERT `PatientArchive` row with snapshot
4. If INSERT fails → abort, return error, patient stays intact

Phase 2 — Cleanup:
1. DELETE ExamOrder rows for this patient
2. DELETE PatientImage rows (files on disk remain)
3. DELETE LabValue rows (via TestResult cascade)
4. DELETE TestResult rows
5. DELETE Patient row
6. If ANY DELETE fails → ROLLBACK entire transaction, archive row stays but patient data remains

#### Scenario: Happy path — PDF downloaded, patient retired

- GIVEN a patient with complete lab data in the waiting room
- WHEN the PDF download endpoint is called for that patient's test result
- AND PDF generation succeeds
- THEN the patient data is archived to `PatientArchive`
- AND the patient + all related rows are cascade-deleted from main tables
- AND the PDF bytes are returned to the client

#### Scenario: PDF generation fails — no archive, no delete

- GIVEN a patient with complete lab data
- WHEN the PDF download endpoint is called
- AND PDF generation raises an error (e.g., WeasyPrint timeout)
- THEN no `PatientArchive` row is created
- AND the patient remains intact in main tables
- AND an HTTP 500 error is returned

#### Scenario: Archive INSERT fails — patient stays, PDF returned

- GIVEN a patient with complete lab data
- WHEN PDF generation succeeds
- BUT the `PatientArchive` INSERT fails (e.g., DB constraint violation)
- THEN the PDF bytes ARE still returned to the client
- AND the patient is NOT deleted from main tables
- AND an error is logged

#### Scenario: PDF download for non-existent test result

- GIVEN no test result with the given ID
- WHEN the PDF endpoint is called
- THEN HTTP 404 is returned
- AND no archive or delete operations occur

#### Scenario: PDF download for patient without lab values

- GIVEN a patient with a TestResult but zero LabValues
- WHEN the PDF endpoint is called
- THEN the system archives the patient (empty lab_values array)
- AND the patient is deleted from main tables
- AND the PDF is generated (with "sin datos" state)

### Requirement: Archive PDF Regeneration

The system MUST support regenerating a PDF from archived snapshot data via a dedicated endpoint.

GET `/reports/archive/{archive_id}/pdf`

1. Load `PatientArchive` by ID
2. Deserialize `snapshot_data` JSON into the same dict format as `TallerService.get_test_result_full()`
3. Call `ReportService.generate_pdf_sync(data)` with the reconstructed dict
4. Return PDF bytes

#### Scenario: Regenerate PDF from archive

- GIVEN an archived patient with ID 42
- WHEN GET `/reports/archive/42/pdf` is called
- THEN the system loads the archive snapshot
- AND generates a PDF with identical content to the original
- AND returns the PDF bytes with `Content-Disposition: attachment`

#### Scenario: Archive not found

- GIVEN no archive with ID 999
- WHEN GET `/reports/archive/999/pdf` is called
- THEN HTTP 404 is returned

#### Scenario: Corrupted snapshot data

- GIVEN an archive with malformed `snapshot_data` JSON
- WHEN GET `/reports/archive/{id}/pdf` is called
- THEN HTTP 500 is returned
- AND an error is logged describing the JSON parse failure

### Requirement: Snapshot Data Compatibility

The `snapshot_data` JSON format MUST match the dict structure returned by `TallerService.get_test_result_full()` so that `ReportService.generate_pdf_sync()` can consume it without modification.

Required top-level keys in snapshot_data:
- `patient`: dict
- `test_result`: dict
- `lab_values`: list[dict]
- `images`: list[dict]
- `summary`: dict (recomputed on regeneration, stored for reference)
- `exam_orders`: list[dict]

#### Scenario: Generated dict matches service output format

- GIVEN a patient archived via retirement flow
- WHEN the snapshot_data is deserialized
- THEN it contains all keys expected by `generate_pdf_sync()`
- AND `lab_values` is a list (even if empty)
- AND `images` is a list (even if empty)

### Requirement: Alembic Migration for PatientArchive

The system SHALL provide an Alembic migration that:
- Creates the `patientarchive` table with all columns specified in the schema
- Adds indexes on `session_code` and `archived_at`
- Is reversible (downgrade drops the table)

#### Scenario: Migration applies cleanly

- GIVEN the current database schema
- WHEN `alembic upgrade head` is run
- THEN the `patientarchive` table exists with all columns
- AND indexes on `session_code` and `archived_at` are created

#### Scenario: Migration reverts cleanly

- GIVEN a database with `patientarchive` table
- WHEN `alembic downgrade -1` is run
- THEN the `patientarchive` table is dropped
- AND no data is lost from other tables

### Acceptance Criteria

1. PDF download endpoint atomically archives and deletes patient data on success
2. Archived PDF regenerates via `/reports/archive/{id}/pdf` with identical content
3. Failed PDF generation does not trigger archive or delete
4. Archive INSERT failure still returns PDF but does not delete patient
5. Alembic migration up/down works on both SQLite and PostgreSQL
6. All existing tests pass; new tests cover archive, regeneration, and error cases
