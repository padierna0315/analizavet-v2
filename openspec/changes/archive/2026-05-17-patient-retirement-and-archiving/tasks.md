# Tasks: Patient Retirement and Archiving

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~450–550 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Foundation + Retirement) → PR 2 (Archiving + Restore + UI) |
| Delivery strategy | exception-ok |
| Chain strategy | single-pr |

Decision needed before apply: No (size:exception approved)
Chained PRs recommended: Resolved to single PR
Chain strategy: single-pr
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Model, migration, and retirement flow (reports router) | Single PR | Tests included; base = main |
| 2 | Archiving status flip, restore, sync dialog option, archive list UI | Single PR | Depends on PR 1; includes templates + reception endpoints |

## Phase 1: Foundation

- [x] 1.1 Create `app/shared/models/patient_archive.py` — `PatientArchive` SQLModel with JSON snapshot field and indexes
- [x] 1.2 Generate Alembic migration `alembic/versions/XXXX_add_patient_archive_table.py` via `--autogenerate`
- [x] 1.3 Add `"archived"` to `Patient.waiting_room_status` docstring comment; no code change needed (field is free-text `str`)

## Phase 2: Retirement (PDF → Archive → Cascade Delete)

- [x] 2.1 In `app/domains/reports/router.py` `download_pdf`: after PDF success, serialize `data` dict → `json.dumps` → INSERT `PatientArchive` → cascade delete ExamOrders → cascade delete Patient (all in single transaction)
- [x] 2.2 Handle rollback: if archive INSERT fails, log error, return PDF but DO NOT delete patient
- [x] 2.3 Add `GET /reports/archive/{archive_id}/pdf` — load archive row, `json.loads(snapshot_data)`, pass to `ReportService.generate_pdf_sync()`, return PDF

## Phase 3: Archiving (Status Flip) and Restore

- [x] 3.1 Add `archive_all_active()`, `restore_all_archived()`, `restore_single_archived()`, `get_archived_patients()` to `app/domains/reception/service.py`
- [x] 3.2 Add `POST /reception/archive`, `POST /reception/restore`, `POST /reception/patient/{id}/restore`, `GET /reception/archived` endpoints to `app/domains/reception/router.py`
- [x] 3.3 In archive_all_active: UPDATE status, then run additive AppSheet sync (same pattern as existing sync)

## Phase 4: UI — Sync Dialog and Archive Views

- [x] 4.1 Add third "📦 Archivar pacientes en recepción" button (blue style) in `app/templates/reception/partials/confirm_sync_reset.html`
- [x] 4.2 Create `app/templates/reception/partials/archive_card.html` — muted-style card with Restaurar button
- [x] 4.3 Create `app/templates/reception/partials/archived_list.html` — grid container for archived cards
- [x] 4.4 Add "📦 Ver archivados (N)" toggle section in `app/templates/taller/reception.html` (or separate archive container)

## Phase 5: Testing

- [x] 5.1 Unit: `PatientArchive` model serialization — create dict matching `get_test_result_full()` output, assert JSON roundtrip preserves all keys
- [x] 5.2 Integration: full retirement flow — create Patient + TR + LVs in test DB, POST to reports endpoint, verify archive row exists, patient row deleted
- [x] 5.3 Integration: PDF generation failure — verify NO archive created, NO patient deleted
- [x] 5.4 Integration: archive_all_active → verify status flips to `"archived"`
- [x] 5.5 Integration: restore single/bulk → verify status back to `"active"`
- [x] 5.6 Integration: archive PDF regeneration → load snapshot, pass to `generate_pdf_sync()`, assert PDF bytes returned
- [x] 5.7 E2E: retired patient excluded from waiting room (existing query pattern auto-filters `waiting_room_status == "active"`)
