# Design: Raw Data Provenance System

## Technical Approach

Single `RawDataLog` table as the audit trail. A `ProvenanceRecorder` abstraction with two capture modes: **sync** for AppSheet (same DB session, no extra commit) and **async fire-and-forget** for Ozelle/Fujifilm (Dramatiq actor with `max_retries=0`). Capture hooks are placed BEFORE parsing at each entry point. Linking `patient_id`/`test_result_id` runs in the processing pipeline for AppSheet; for Ozelle/Fujifilm it's lazy — done at archive time.

## Architecture Decisions

### Decision: ProvenanceRecorder as capture facade
| Option | Tradeoff | Decision |
|--------|----------|----------|
| Inline capture per entry point | Duplication, tight coupling to I/O | ✗ |
| **ProvenanceRecorder class** | Single interface, testable, swaps sync/async | ✓ |

### Decision: Dramatiq actor for async capture (not BackgroundTasks)
| Option | Tradeoff | Decision |
|--------|----------|----------|
| FastAPI BackgroundTasks | Tied to HTTP lifecycle — TCP servers have none | ✗ |
| **Dramatiq actor (max_retries=0)** | Consistent with existing pattern; no retry = true fire-and-forget | ✓ |
| `asyncio.create_task` | No durability, lost on crash | ✗ |

### Decision: Lazy linking for Ozelle/Fujifilm, inline for AppSheet
| Option | Tradeoff | Decision |
|--------|----------|----------|
| UUID token threaded through pipeline | Additional plumbing TCP → Dramatiq → actor | ✗ |
| **AppSheet inline backfill + Ozelle/Fujifilm lazy at archive** | AppSheet has session context; adapters don't | ✓ |
| Match by (source, received_at window) | Race: capture write may not complete before backfill runs | ✗ |

### Decision: session_code as the linking key
| Option | Tradeoff | Decision |
|--------|----------|----------|
| RawDataLog.id threaded through | Requires modifying all pipeline interfaces | ✗ |
| **session_code** | Already indexed, naturally available in all sources, survives async gap | ✓ |

## Data Flow

```ascii
AppSheet:
  route → fetch() → response.json()
                     │
                     ├── capture_sync(session, raw_json, source=APPSHEET)
                     │       ↓ RawDataLog (same transaction, no flush)
                     │
                     └── parse → sync_from_appsheet()
                                  │
                                  └── after each patient processed:
                                      update RawDataLog SET patient_id, status='linked'
                                      WHERE session_code = patient.session_code

Ozelle/Fujifilm TCP:
  handle_client() → decode bytes
                     │
                     ├── capture_async(raw_str, source, metadata)
                     │       ↓ Dramatiq (fire-and-forget, max_retries=0)
                     │       record_raw_data actor → RawDataLog (sync_engine)
                     │
                     └── parse + enqueue main actor → pipeline()
                                                        │
                                                        └── patient_id + test_result_id known
                                                            (no backfill — lazy at archive)

Archive (PDF download):
  get_test_result_full()
    ↓
  query RawDataLog WHERE patient_id = ? OR session_code = ?
    ↓
  include in PatientArchive.snapshot_data.raw_data_logs[]
  update RawDataLog SET status='archived' (no delete)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/shared/models/raw_data_log.py` | Create | `RawDataLog` SQLModel — all columns, indexes, no FK cascade |
| `app/domains/provenance/__init__.py` | Create | Init package |
| `app/domains/provenance/recorder.py` | Create | `ProvenanceRecorder` — `capture_sync()` + `capture_async()` |
| `app/domains/provenance/actor.py` | Create | `record_raw_data` Dramatiq actor (fire-and-forget) |
| `app/domains/provenance/service.py` | Create | `ProvenanceService` — query/link/archive operations |
| `app/services/appsheet.py` | Modify | Capture raw JSON in `fetch_active_patients()`, backfill in `sync_from_appsheet()` |
| `app/satellites/ozelle/mllp_server.py` | Modify | Capture raw HL7 before `parse_hl7_message()` |
| `app/satellites/fujifilm/adapter.py` | Modify | Capture raw TCP line before `parse_fujifilm_message()` |
| `app/domains/patients/router.py` | Modify | Add HTMX route for raw data view + partial |
| `app/templates/patients/detail.html` | Modify | Add "Ver datos crudos" button |
| `app/templates/patients/raw_data_fragment.html` | Create | HTMX partial — source-grouped cards with scrollable payload |
| `app/domains/reports/router.py` | Modify | Include raw_data_logs in archive snapshot |
| `alembic/versions/xxxx_add_raw_data_log_table.py` | Create | Migration |
| `alembic/env.py` | Modify | Import `RawDataLog` |
| `app/tasks/broker.py` | Modify | Import `app.domains.provenance.actor` |

## Interfaces / Contracts

```python
# Recorder facade
class ProvenanceRecorder:
    @staticmethod
    async def capture_sync(
        session: AsyncSession, source: RawDataSource,
        raw_data: str, metadata: dict | None = None,
    ) -> None:
        """Sync capture — reuses existing session, no extra commit."""

    @staticmethod
    def capture_async(
        source: RawDataSource, raw_data: str,
        metadata: dict | None = None,
    ) -> None:
        """Fire-and-forget via Dramatiq. Never blocks, never retries."""

# Dramatiq actor (max_retries=0)
@dramatiq.actor(max_retries=0, time_limit=10000)
def record_raw_data(source: str, raw_data: str, metadata_json: str | None) -> None: ...

# Sync backfill in AppSheet flow
class ProvenanceService:
    @staticmethod
    async def link_to_patient(
        session: AsyncSession, session_code: str,
        patient_id: int, test_result_id: int | None = None,
    ) -> None: ...

# RawDataLog model (key fields)
class RawDataLog(SQLModel, table=True):
    __tablename__ = "rawdatalog"
    id: int | None = Field(default=None, primary_key=True)
    source: str  # Enum via validation
    raw_data: str  # TEXT — supports up to 1MB
    received_at: datetime
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = None
    patient_id: int | None = Field(default=None, foreign_key="patient.id")
    test_result_id: int | None = Field(default=None, foreign_key="testresult.id")
    session_code: str | None = Field(default=None, index=True)
    status: str = "pending"  # pending → linked → archived
    error_message: str | None = None
    metadata: str | None = None  # JSON blob
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ProvenanceRecorder.capture_sync/async` | Mock session, verify RawDataLog created |
| Unit | `record_raw_data` actor | Stub broker, verify DB write |
| Unit | `ProvenanceService.link_to_patient` | In-memory DB, verify update |
| Integration | AppSheet capture + backfill | Wire full flow: mock HTTP, verify RawDataLog + patient link |
| Integration | Ozelle TCP + async capture | Stub broker + in-memory DB, verify capture before parse |
| Integration | Archive includes raw_data_logs | Create RawDataLog, archive, verify JSON snapshot contains it |
| E2E | Patient detail page shows raw data | HTMX request to new endpoint, verify HTML content |

## Migration

```python
# Alembic migration — create rawdatalog table
def upgrade():
    op.create_table('rawdatalog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('raw_data', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('test_result_id', sa.Integer(), nullable=True),
        sa.Column('session_code', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['test_result_id'], ['testresult.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_rawdatalog_patient_id', 'rawdatalog', ['patient_id'])
    op.create_index('ix_rawdatalog_session_code', 'rawdatalog', ['session_code'])
    op.create_index('ix_rawdatalog_source', 'rawdatalog', ['source'])

def downgrade():
    op.drop_table('rawdatalog')
```

## Open Questions

- [ ] Should Ozelle/Fujifilm capture use `datetime.now(timezone.utc)` at the TCP server or use the parsed timestamp? Decision: use `now()` at entry point for `received_at`, since we want the true arrival time.
- [ ] Concurrent backfill at archive time: if two PDF downloads happen for the same patient, both try to update RawDataLog rows — is this safe? (Yes — idempotent update, `status='archived'`)
