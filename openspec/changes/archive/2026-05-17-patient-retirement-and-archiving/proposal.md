# Proposal: Patient Retirement and Archiving

## Intent

Two problems: (1) PDF download never removes patients from reception — they accumulate with no lifecycle end, and regenerating PDFs from gone patients is impossible. (2) Sync dialog has no graceful way to clear reception without permanent cascade DELETE.

## Scope

### In Scope
- `PatientArchive` table with full snapshot of Patient + TestResult + LabValue + PatientImage + ExamOrder
- PDF retirement: on success → archive first → cascade delete from main tables
- PDF regeneration endpoint from archived data
- "Archivar pacientes" option in sync dialog → `waiting_room_status = 'archived'`
- "Restaurar" action → flip back to `'active'`
- Alembic migration for new table and status values
- Filter archived patients from all waiting room queries

### Out of Scope
- Search/browse UI for historical patients
- Batch PDF regeneration
- Archive cleanup/purge
- PatientRegistry/turno integration

## Capabilities

### New Capabilities
- `patient-archive`: Permanent retirement — full data snapshot + cascade delete + PDF regeneration from archive
- `patient-archiving`: Temporary soft-hide via status flag, reversible

### Modified Capabilities
None — no existing specs to modify.

## Approach

**Retirement**: New `PatientArchive` table stores JSON snapshots of Patient + all FK-related rows. Flow: (1) generate PDF, (2) serialize all data to PatientArchive row, (3) cascade-delete patient from main tables. Regeneration reads from archive via `TallerService.get_archived_test_result_full()`.

**Archiving**: Add `'archived'` to `waiting_room_status` enum. Single UPDATE status = no data movement. All `WHERE waiting_room_status == 'active'` queries automatically exclude archived. Restore is same UPDATE reversed.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/domains/patients/models.py` | Modified | Add `archived` to waiting_room_status doc/type |
| `app/shared/models/` | New | `PatientArchive` model (snapshot table) |
| `app/domains/reports/router.py` | Modified | Hook archive-after-PDF + archive regeneration endpoint |
| `app/domains/reports/service.py` | Modified | Add archive-save step after PDF success |
| `app/domains/taller/service.py` | Modified | Add `get_archived_test_result_full()` |
| `app/domains/reception/router.py` | Modified | New `/archive`, `/restore` endpoints |
| `app/domains/reception/service.py` | Modified | New archive/restore service methods |
| `app/templates/reception/partials/confirm_sync_reset.html` | Modified | Add third "Archivar" option |
| `alembic/versions/` | New | Migration for PatientArchive table |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| PDF succeeds, archive fails → patient lost | Low | Two-phase: archive first, PDF after. Rollback archive on PDF failure. |
| Archived patients slow queries | Low | Add index on `waiting_room_status`; queries already filter by it |
| UX confusion with third sync option | Med | Clear labels: "Archivar pacientes en recepción" + confirmation text |
| ExamOrder FK on archive deletion | Low | Copy ExamOrder to archive + include in cascade delete |

## Rollback Plan

- **Retirement**: Restore from `PatientArchive` → re-insert to main tables (idempotent — check by session_code)
- **Archiving**: `UPDATE patient SET waiting_room_status = 'active' WHERE waiting_room_status = 'archived'`
- **Schema**: Alembic downgrade drops `patientarchive` table

## Dependencies

- Alembic (already configured)
- WeasyPrint (no change)

## Success Criteria

- [ ] PDF download archives patient data AND removes from reception on success
- [ ] Archived PDFs regenerate via `/reports/archive/{archive_id}/pdf`
- [ ] "Archivar pacientes" in sync dialog sets `waiting_room_status = 'archived'`, removes from grid
- [ ] "Restaurar" button flips archived patients back to `'active'`
- [ ] Archived patients never appear in waiting room queries
- [ ] Alembic migration up/down works cleanly
- [ ] All existing tests pass + new tests for archive/restore flows
