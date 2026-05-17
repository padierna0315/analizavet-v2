# Raw Data Provenance Specification

## Purpose

Capture, store, and retrieve raw incoming messages from AppSheet, Ozelle, and Fujifilm *before* parsing — preserving provenance for audit, debugging, and replay without impacting the live pipeline.

## Requirements

### Requirement: RawDataLog Model

The system MUST provide a `RawDataLog` table.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK, auto | |
| source | Enum(appsheet, ozelle, fujifilm) | Source discriminator |
| raw_data | Text | Full payload (JSON, HL7, or TCP text) |
| received_at | DateTime, UTC | Original message arrival |
| captured_at | DateTime, UTC | When this row was written |
| processed_at | DateTime, UTC, nullable | When linked processing completed |
| patient_id | Integer, nullable, indexed | FK to Patient (set when known) |
| test_result_id | Integer, nullable, indexed | FK to TestResult |
| session_code | String, nullable, indexed | Grouping identifier |
| status | Enum(pending, linked, archived) | Lifecycle state |
| error_message | Text, nullable | Capture error detail |
| metadata | JSON/Text, nullable | Extra context (encoding, content_type) |

`raw_data` MUST support up to 1 MB. No application-layer compression — SQLite storage is sufficient.

#### Scenario: AppSheet JSON captured before parsing

- GIVEN a valid AppSheet JSON response
- WHEN the response is captured BEFORE parsing into Patient/ExamOrder
- THEN a `RawDataLog` row is created with source="appsheet" and the full JSON

#### Scenario: Ozelle HL7 captured before parsing

- GIVEN a valid HL7 message via MLLP
- WHEN the raw HL7 string is captured BEFORE parsing
- THEN a `RawDataLog` row is created with source="ozelle" and the full HL7 text

#### Scenario: Fujifilm TCP captured before parsing

- GIVEN a valid Fujifilm TCP message
- WHEN the raw text is captured BEFORE processing
- THEN a `RawDataLog` row is created with source="fujifilm" and the full message

#### Scenario: Large HL7 stored without error

- GIVEN an Ozelle HL7 message exceeding 100 KB
- WHEN the message is captured
- THEN it is stored successfully in the TEXT column
- AND main processing time variance is within 5% of baseline

### Requirement: Capture Must Not Block Pipeline

AppSheet capture SHALL use a synchronous write reusing the existing DB session — no extra commit. Ozelle and Fujifilm capture SHALL use fire-and-forget Dramatiq actors (no retry, no backpressure).

#### Scenario: AppSheet sync capture

- GIVEN an incoming AppSheet request
- WHEN the request is processed
- THEN raw JSON capture uses the current DB session with no separate commit

#### Scenario: Ozelle async fire-and-forget

- GIVEN an incoming HL7 message
- WHEN the message is parsed
- THEN a Dramatiq actor is enqueued with the raw HL7 text
- AND processing continues without waiting for the actor

#### Scenario: Fujifilm async fire-and-forget

- GIVEN an incoming Fujifilm TCP message
- WHEN the message is processed
- THEN a Dramatiq actor is enqueued with the raw message text
- AND processing continues without waiting for the actor

### Requirement: Linking to Processed Entities

`patient_id` and `test_result_id` MUST be nullable — raw data often arrives before entity creation (concurrent Fujifilm/Ozelle flow). Linking MAY occur via backfill at archive time. No FK cascade — raw data SHALL survive deletion.

#### Scenario: Patient identity resolved after capture

- GIVEN a `RawDataLog` row with NULL patient_id
- WHEN the patient identity is resolved from the parsed message
- THEN the row's patient_id is updated accordingly

### Requirement: Error Isolation

Capture failure MUST NOT propagate to the main pipeline. Sync failures are logged and swallowed. Async failures drop silently with no retry.

#### Scenario: AppSheet capture DB failure

- GIVEN an AppSheet JSON response being processed
- WHEN the raw data capture write fails
- THEN the main request succeeds normally
- AND the error is logged

#### Scenario: Dramatiq actor failure

- GIVEN an Ozelle HL7 message being processed
- WHEN the raw capture actor fails
- THEN the original HL7 processing is unaffected
- AND no retry is spawned

### Requirement: UI — Raw Data View

The UI MUST expose a "Ver datos crudos" entry from the patient detail page. It SHOW show all `RawDataLog` rows for that patient, grouped by source, with the raw payload in a scrollable preformatted block and timestamps visible.

#### Scenario: User views raw data per patient

- GIVEN a patient with raw data from AppSheet and Ozelle
- WHEN the user clicks "Ver datos crudos"
- THEN two source-grouped cards are shown with full raw payloads and timestamps

### Requirement: Archive Integration

On patient retirement, `RawDataLog` rows MUST be included in the `PatientArchive.snapshot_data` under a `raw_data_logs` array. Original rows remain in the `RawDataLog` table (no cascade delete).

#### Scenario: Raw data archived on retirement

- GIVEN a patient with 3 `RawDataLog` rows
- WHEN the patient is retired
- THEN `PatientArchive.snapshot_data` contains a `raw_data_logs` array with all 3 rows
- AND original `RawDataLog` rows persist in the database

### Requirement: Alembic Migration

The system SHALL provide an Alembic migration to create `rawdatalog` with all columns, indexes on `patient_id`, `test_result_id`, `session_code`, and `source`, and be reversible.

#### Scenario: Migration applies cleanly

- GIVEN the current schema
- WHEN `alembic upgrade head` is run
- THEN `rawdatalog` table exists with all columns and indexes

#### Scenario: Migration reverts cleanly

- GIVEN a database with `rawdatalog`
- WHEN `alembic downgrade -1` is run
- THEN `rawdatalog` is dropped without affecting other tables
