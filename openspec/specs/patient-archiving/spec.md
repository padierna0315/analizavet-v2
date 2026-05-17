# Patient Archiving Specification

## Purpose

Define the temporary soft-hide flow: archive patients from the waiting room via status flag without data movement, and restore them back to active.

## Requirements

### Requirement: Archived Status Value

The system MUST support `waiting_room_status = "archived"` as a valid status value on the `Patient` model.

Existing valid values: `active`, `deleted`, `pdf_generated`
New valid value: `archived`

All existing queries filtering by `waiting_room_status == "active"` MUST automatically exclude archived patients. No query changes needed for exclusion — the filter already exists.

#### Scenario: Archived patient excluded from waiting room

- GIVEN a patient with `waiting_room_status = "archived"`
- WHEN `get_waiting_room_patients()` is called
- THEN the patient is NOT included in the results

#### Scenario: Archived patient excluded from sync check

- GIVEN 5 active patients and 3 archived patients
- WHEN the sync check endpoint queries `Patient.waiting_room_status == "active"`
- THEN it returns count = 5

### Requirement: Archive Patients via Sync Dialog

The sync dialog (`confirm_sync_reset.html`) MUST offer a third option: "Archivar pacientes en recepción".

This option:
- Sets `waiting_room_status = "archived"` for ALL patients currently with `waiting_room_status = "active"`
- Does NOT delete any data
- Then proceeds with normal AppSheet sync (additive, no reset)
- Is clearly labeled to distinguish from "Reset" (permanent delete) and "Add only" (keep active)

Post-archive, the dialog triggers `refreshReceptionGrid` via HTMX trigger so the grid clears.

#### Scenario: Archive then sync — happy path

- GIVEN 10 active patients in the waiting room
- WHEN the user clicks "Archivar pacientes en recepción" in sync dialog
- THEN all 10 patients get `waiting_room_status = "archived"`
- AND AppSheet sync runs without resetting
- AND the waiting room grid refreshes showing only the newly synced patients

#### Scenario: Empty waiting room archive

- GIVEN 0 active patients in the waiting room
- WHEN the user clicks the archive button
- THEN the archive operation sets 0 rows (no-op)
- AND the sync proceeds normally

### Requirement: Restore Archived Patients

A "Restaurar" action MUST be available to flip archived patients back to active.

POST `/reception/restore` — restores ALL archived patients.
OR POST `/reception/patient/{patient_id}/restore` — restores a single patient.

Restore is a simple UPDATE: `SET waiting_room_status = "active"` on the matching patient row(s). No data migration needed.

#### Scenario: Restore all archived patients

- GIVEN 5 archived patients in the database
- WHEN POST `/reception/restore` is called
- THEN all 5 patients now have `waiting_room_status = "active"`
- AND they reappear in the waiting room grid

#### Scenario: Restore single archived patient

- GIVEN an archived patient with ID 7
- WHEN POST `/reception/patient/7/restore` is called
- THEN patient 7 has `waiting_room_status = "active"`
- AND only patient 7 is affected
- AND if patient 7 was already active, the call is a no-op (returns success)

#### Scenario: Restore non-existent patient

- GIVEN no patient with ID 9999
- WHEN POST `/reception/patient/9999/restore` is called
- THEN HTTP 404 is returned

### Requirement: UI — Archive Button in Sync Dialog

The sync dialog (`confirm_sync_reset.html`) MUST include a third button positioned between "Reset" and "Cancel":

```html
<button class="btn-archive"
  hx-post="/reception/archive"
  hx-target="#sync-status"
  hx-swap="innerHTML"
  hx-on::after-request="document.getElementById('modal-container').innerHTML = ''">
  📦 Archivar pacientes en recepción
</button>
```

Button style: distinct from both `.btn-delete` (danger) and `.btn-cancel` (neutral). Use a blue/tertiary style with clear icon.

The confirmation text MUST be updated to mention the third option.

#### Scenario: Dialog shows three options

- GIVEN the sync dialog is displayed
- THEN it shows three buttons: "Limpiar y Sincronizar", "Archivar pacientes en recepción", "Solo agregar nuevos", "Cancelar"
- AND the middle option has distinct styling

### Requirement: UI — Restore Button

An "Archivados" section or button MUST be available in the Taller reception view to show archived patients and restore them.

A link/button: "📦 Ver archivados (N)" that toggles display of archived patient cards.

Each archived patient card in the archive view shows a "Restaurar" button that calls the single-patient restore endpoint and moves the card back to active grid.

#### Scenario: View archived patients

- GIVEN 3 archived patients in the database
- WHEN the user clicks "Ver archivados"
- THEN the system loads archived patients
- AND displays their cards in a muted style (lower opacity, gray border)

#### Scenario: Restore from archived view

- GIVEN an archived patient card displayed in the archive view
- WHEN the user clicks "Restaurar" on that card
- THEN POST `/reception/patient/{id}/restore` is called
- AND the card is removed from archive view
- AND the patient card appears in the active waiting room grid

### Requirement: POST /reception/archive

New endpoint to archive all active patients.

- Method: POST
- Path: `/reception/archive`
- Action: UPDATE Patient SET waiting_room_status = "archived" WHERE waiting_room_status = "active"
- Returns: HTMX success message + triggers `refreshReceptionGrid`
- Error: Returns error HTML on DB failure

### Requirement: POST /reception/patient/{patient_id}/restore

New endpoint to restore a single archived patient.

- Method: POST
- Path: `/reception/patient/{patient_id}/restore`
- Action: UPDATE Patient SET waiting_room_status = "active" WHERE id = patient_id
- Returns: HTMX partial (patient card) for OOB swap into grid
- 404: If patient not found

### Requirement: POST /reception/restore

New endpoint to restore ALL archived patients.

- Method: POST
- Path: `/reception/restore`
- Action: UPDATE Patient SET waiting_room_status = "active" WHERE waiting_room_status = "archived"
- Returns: HTMX success message + triggers `refreshReceptionGrid`

### Acceptance Criteria

1. Archived patients are excluded from all waiting room queries
2. Sync dialog has a working third option that archives + syncs
3. Archived patients can be restored individually or in bulk
4. Restored patients reappear in the waiting room grid
5. Alembic migration adds no new table (status change only)
6. All existing tests pass; new tests cover archive/restore endpoints
