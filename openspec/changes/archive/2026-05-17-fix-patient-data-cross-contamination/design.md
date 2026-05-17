# Design: Fix Patient Data Cross-Contamination

## Technical Approach

Single-file bugfix in `app/domains/reception/service.py` with three changes:
1. **Line 105**: Remove `raw_string` as session_code fallback — if no `session_code`, skip to normalization directly.
2. **Fujifilm fallback (lines 184-187)**: Replace `.first()` with `.all()` + uniqueness guard (exactly 1 match → reuse; 0 or ≥2 → create new).
3. **Ozelle/File fallback (lines 246-249)**: Same pattern.

No helper extraction — the two branches have different logfire contexts and variable names. Extracting would add complexity for zero gain.

## Architecture Decisions

### Decision: Replace `.first()` with `.all()` + length check

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `.first()` (current) | Picks arbitrary row when ≥2 matches → cross-contamination | ❌ Rejected |
| `.all()` + `len() == 1` guard | Safe: known 1 → match; 0 or ≥2 → create new | ✅ Selected |
| `scalar_one_or_none()` | Would raise if ≥2 rows — noisier than needed | ❌ Rejected |

`scalar_one_or_none()` would raise `MultipleResultsFound` on ≥2 matches. The spec says create new in that case — an exception would abort the request with a 500. `.all()` + check is explicit and handles all three cases without exceptions.

### Decision: Remove `raw_string` from lookup_code at line 105

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `raw_input.session_code or raw_input.raw_string` (current) | Falls back to `raw_string` as a lookup code → wrong match | ❌ Rejected |
| Only `raw_input.session_code` | When session_code is absent, skip block entirely | ✅ Selected |
| Allow `None` session_code but guard | Same effect but more code | ❌ Rejected |

The spec requirement is clear: `raw_string` MUST NOT serve as lookup code. The simplest correct fix is to only enter the session_code block when `raw_input.session_code` is truthy.

### Decision: No shared helper for fallback branches

Both branches (Fujifilm, Ozelle/File) follow the same `.all()` + guard pattern, but:
- Different logfire context strings
- Different variable names (`fuji_match` vs `ozelle_match`)
- Different backfill logic (both backfill `session_code`, but Fujifilm has separate species/sex overrides)

A shared helper would need 3+ parameters or a callback for the divergent parts. The current duplication is acceptable and keeps each path independently readable.

## Data Flow

```
receive(raw_input)
  │
  ├─ [session_code present?]
  │     ├─ Yes → query Patient.session_code == raw_input.session_code
  │     │         ├─ Found → return existing (created=False)
  │     │         └─ Not found → continue to normalize
  │     └─ No → skip directly to normalize (NO raw_string lookup)
  │
  ├─ normalize raw_string → norm_name, norm_owner
  │
  ├─ [source == FUJIFILM?]
  │     ├─ query Patient.normalized_name == norm_name
  │     │    .all() → len == 1 → reuse existing → return (created=False)
  │     │    .all() → len != 1 → fall through to create
  │     └─ not Fujifilm → skip
  │
  ├─ [source in (OZELLE, FILE)?]
  │     ├─ query Patient.normalized_name == norm_name
  │     │    .all() → len == 1 → reuse existing → return (created=False)
  │     │    .all() → len != 1 → fall through to create
  │     └─ not Ozelle/File → skip
  │
  ├─ baul._find_existing(norm_name, norm_owner, species)
  │     ├─ Found → merge → return (created=False)
  │     └─ Not found → continue
  │
  └─ baul.register(...) → create new patient → return (created=True)
```

Critical property: the Fujifilm and Ozelle/File fallbacks now produce the same result for 0 and ≥2 matches — both fall through to the baul dedup flow, which correctly creates a new patient.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/domains/reception/service.py` | Modify | Fix line 105 lookup, add uniqueness guards in two fallback blocks |

## Interfaces / Contracts

No new interfaces, types, or public API changes. Internals only:
- Rename `fuji_match` → `fuji_matches` (scalar → list)
- Rename `ozelle_match` → `ozelle_matches` (scalar → list)

## Control Flow After Fix

### Line 105 (session_code lookup)

```python
# Before:
lookup_code = raw_input.session_code or raw_input.raw_string
stmt = select(Patient).where(Patient.session_code == lookup_code)

# After:
if raw_input.session_code:
    stmt = select(Patient).where(Patient.session_code == raw_input.session_code)
    result = await session.execute(stmt)
    existing_patient = result.scalar_one_or_none()
    if existing_patient:
        # ... existing reuse logic (lines 110-164) ...
        return BaulResult(...)
# No else — continue to normalization
```

### Fujifilm fallback (lines 184-187)

```python
# Before:
fuji_match = result.scalars().first()
if fuji_match:
    # ... reuse ...

# After:
fuji_matches = result.scalars().all()

if len(fuji_matches) == 1:
    fuji_match = fuji_matches[0]
    # ... existing reuse logic (lines 189-241) ...
    return BaulResult(...)

# logfire: log why we're creating new (0 or ≥2 matches)
# Continue to creation flow
```

### Ozelle/File fallback (lines 246-249)

```python
# Before:
ozelle_match = result.scalars().first()
if ozelle_match:
    # ... reuse ...

# After:
ozelle_matches = result.scalars().all()

if len(ozelle_matches) == 1:
    ozelle_match = ozelle_matches[0]
    # ... existing reuse logic (lines 251-304) ...
    return BaulResult(...)

# logfire: log why we're creating new
# Continue to creation flow
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Line 105 — session_code absent → skip lookup | Mock `session.execute` — verify no call when `session_code` is None |
| Unit | Fujifilm: 0 matches → creates new | Mock query returning `[]` — verify new patient created |
| Unit | Fujifilm: 1 match → reuses | Mock query returning `[patient]` — verify `created=False` |
| Unit | Fujifilm: 2 matches → creates new | Mock query returning `[p1, p2]` — verify new patient created |
| Unit | Ozelle/File: same 3 cases | Same approach as Fujifilm |
| Integration | Verify `len(matches) == 1` path matches current `.first()` behavior | Existing pytest suite |

Existing tests should continue passing. See also `app/domains/reception/test_service.py` for current test structure.

**Key insight**: the 0-match case currently falls through to creation via `.first()` returning `None`. The `.all()` + guard preserves that same behavior. Only the ≥2 case changes — `.first()` would silently pick one, now we create new.

## Migration / Rollout

No migration required. Schema unchanged. Single commit, single file.

## Open Questions

- None. Spec and approach are fully resolved.
