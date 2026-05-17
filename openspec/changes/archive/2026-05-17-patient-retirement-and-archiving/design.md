# Design: Patient Retirement and Archiving

## Technical Approach

Two independent features sharing the same change boundary:

**Retirement** (permanent): New `PatientArchive` table stores JSONB snapshot. PDF download flow becomes 3-phase: (1) fetch full data + generate PDF, (2) INSERT archive with snapshot, (3) cascade DELETE main rows. The `data` dict from `TallerService.get_test_result_full()` is the snapshot format — zero transformation needed.

**Archiving** (temporary soft-hide): Single `waiting_room_status` UPDATE from `'active'` to `'archived'`. No data movement. Existing queries with `WHERE waiting_room_status == 'active'` auto-exclude archived patients — no query changes.

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| Snapshot as JSONB (Postgres) / TEXT (SQLite) vs separate normalization | JSONB keeps archive fast, self-contained, regeneratable. Normalization buys nothing — archive is write-once/read-rarely | **JSONB/TEXT blob** — follows existing `_JsonListType` pattern for polymorphic JSON storage |
| Archive-before-PDF vs PDF-before-archive | PDF fails sometimes (WeasyPrint/OOM). Archive-before-PDF means patient deleted even when PDF fails → data loss | **PDF first, archive second** — PDF bytes in memory → archive INSERT → cascade DELETE. If archive fails, patient stays and PDF was already returned |
| New column `'archived'` vs separate table for soft-hide | Separate table means data duplication + complex queries. Status flag is one UPDATE | **Status flag** — zero new tables, zero query changes |
| Cascade delete ExamOrders on retirement | Current `Patient.exam_orders` has **no cascade** — need manual delete before Patient DELETE | **Manual delete** — load all ExamOrders by patient_id, delete them, then delete Patient (ORM cascade handles TR/LV/images) |

## Data Flow

**Retirement (PDF download)**:
```
Client → GET /reports/{result_id}/pdf
  → TallerService.get_test_result_full() → data dict
  → ReportService.generate_pdf_sync(data) → PDF bytes
  → [NEW] Serialize data → INSERT PatientArchive
  → [NEW] DELETE ExamOrders WHERE patient_id
  → [NEW] DELETE Patient (ORM cascade → TR + LV + images)
  → Return PDF Response
```

**Archive regeneration**:
```
Client → GET /reports/archive/{archive_id}/pdf
  → SELECT PatientArchive WHERE id
  → json.loads(snapshot_data) → data dict
  → ReportService.generate_pdf_sync(data) → PDF bytes  (*zero changes to generate_pdf_sync*)
  → Return PDF Response
```

**Archiving (sync dialog)**:
```
Client → POST /reception/archive
  → UPDATE Patient SET waiting_room_status='archived' WHERE status='active'
  → run AppSheet sync (additive, no reset)
  → return HTMX + HX-Trigger: refreshReceptionGrid
```

**Restore**:
```
Client → POST /reception/patient/{id}/restore (single)
       → POST /reception/restore (bulk)
  → UPDATE Patient SET waiting_room_status='active' WHERE condition
  → return HTMX partial (single) / HX-Trigger (bulk)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/shared/models/patient_archive.py` | Create | `PatientArchive` SQLModel — id, session_code (idx), patient_name, owner_name, species, archived_at, snapshot_data (JSON), original_patient_id, original_test_result_id |
| `app/domains/reports/router.py` | Modify | Add archive step + cascade delete after PDF success in `download_pdf`. Add `GET /reports/archive/{archive_id}/pdf` for regeneration |
| `app/domains/reception/service.py` | Modify | Add `archive_all_active()`, `restore_all_archived()`, `restore_single_archived()` methods |
| `app/domains/reception/router.py` | Modify | Add `POST /reception/archive`, `POST /reception/patient/{id}/restore`, `POST /reception/restore` endpoints |
| `app/templates/reception/partials/confirm_sync_reset.html` | Modify | Add third "Archivar" button between reset and cancel |
| `app/templates/reception/partials/archive_card.html` | Create | Patient card partial for archived view (muted style + Restaurar button) |
| `app/templates/reception/partials/archived_list.html` | Create | Container partial for archived patients grid |
| `app/templates/taller/reception.html` | Modify | Add "📦 Ver archivados (N)" toggle section |
| `alembic/versions/XXXX_add_patient_archive_table.py` | Create | Auto-generated migration for `patientarchive` table with indexes |

## Interfaces / Contracts

**PatientArchive model** (`app/shared/models/patient_archive.py`):
```python
class PatientArchive(SQLModel, table=True):
    __tablename__ = "patientarchive"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_code: Optional[str] = Field(default=None, index=True)
    patient_name: str
    owner_name: str
    species: str
    archived_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_data: str  # JSON string — same format as get_test_result_full() return
    original_patient_id: Optional[int] = Field(default=None)
    original_test_result_id: Optional[int] = Field(default=None)
```

**JSON snapshot format**: Exactly the dict returned by `TallerService.get_test_result_full()` — keys: `patient`, `test_result`, `lab_values` (list), `images` (list), `summary`, `interpretations`, `exam_orders`.

**generate_pdf_sync(data) — unchanged**: Already accepts the `data: dict` in the same format. Archive regeneration just loads snapshot → `json.loads()` → pass directly.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `PatientArchive` model serialization | Create dict matching get_test_result_full() output, serialize to JSON, assert all keys/types preserved |
| Unit | `generate_pdf_sync` with archive data | Load snapshot JSON, pass to generate_pdf_sync(), assert PDF bytes returned (no DB dependency) |
| Integration | Archive INSERT + cascade delete | Create full Patient + TR + LVs + images in test DB. POST to reports endpoint. Verify archive row exists and patient row deleted |
| Integration | Archiving (status flip) | INSERT active patients, POST `/reception/archive`, verify status='archived' |
| Integration | Restore single/bulk | Flip to archived, POST restore, verify status='active' |
| E2E | Full PDF download → archive → regenerate | Browser-driven: download PDF → confirm patient gone → regenerate from archive → PDF identical |
| E2E | Sync dialog archive option | HTMX interaction: check third button exists, click, grid refreshes, patients gone |

## Migration / Rollout

**Alembic revision** — single `alembic revision --autogenerate -m "add_patient_archive_table"`. Creates `patientarchive` table with indexes on `session_code` and `archived_at`. Reversible (downgrade drops table).

**Existing data**: No data migration needed — `PatientArchive` is a new table, only new records written.

**Rollback**:
- Retirement rollback: `INSERT INTO patient ... FROM PatientArchive` (restore from snapshot)
- Archiving rollback: `UPDATE patient SET waiting_room_status='active' WHERE waiting_room_status='archived'`
- Schema rollback: Alembic downgrade

## Open Questions

- None
