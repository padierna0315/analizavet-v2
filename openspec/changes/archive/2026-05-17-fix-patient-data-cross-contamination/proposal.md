# Proposal: Fix Patient Data Cross-Contamination

## Intent

Critical bug: patients sharing the same name (e.g., "Kiara", "Rio") receive wrong lab results. Root cause: when `session_code` is absent, `app/domains/reception/service.py` matches patients purely by `normalized_name` via `.first()` — picking whichever the DB returns first. This cross-contaminates patients with common names (Luna, Max, Rocky, Coco, etc.).

## Scope

### In Scope
- Replace `.first()` name-only fallback with `.all()` + uniqueness check in both Fujifilm (lines 184-187) and Ozelle/File (lines 246-249) branches
- If ≥2 patients share the name → create new patient (safe isolation)
- If 0 patients → continue existing creation flow
- If exactly 1 → safe match as before
- Optimize wasted query at line 105 (`lookup_code = raw_input.session_code or raw_input.raw_string`)

### Out of Scope
- Ozelle HL7 PID[3] handling (separate concern, works correctly)
- Broader deduplication or merge logic
- session_code generation strategy

## Capabilities

### New Capabilities
None — pure bugfix, no spec-level behavior change.

### Modified Capabilities
None — requirements unchanged, only implementation correctness.

## Approach

**Guard clause pattern**: replace each `result.scalars().first()` with `result.scalars().all()`, then apply a 3-way branch:
- exactly 1 → proceed (current flow unchanged)
- 0 → continue to creation (existing logic at line 366)
- ≥2 → treat as "not found" and create new patient (safe isolation)

Same logic for both Fujifilm and Ozelle/File. Extract into a `_resolve_name_match(patients, norm_name, raw_input, session)` helper if both branches converge.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/domains/reception/service.py` | Modified | Replace `.first()` with `.all()` + guard clause in 2 fallback blocks (lines 181-249). Optional: deduplicate fallback logic into shared helper. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| False duplicate when same patient has 2 DB rows (e.g., race condition) | Low | Create new patient — deduplication is a separate concern. Safe to create a duplicate rather than cross-contaminate. |
| Regression in existing matching | Low | Uniqueness-preserving: exact-1 match behaves identically to `.first()`. |

## Rollback Plan

Revert the single commit. The change is localized to one file with no migration or schema changes.

## Dependencies

None.

## Success Criteria

- [ ] Fujifilm fallback: when 2+ patients share `normalized_name` and no `session_code` match, a NEW patient is created instead of picking the wrong one
- [ ] Ozelle/File fallback: same guard applied
- [ ] Single match still works identically to current behavior
- [ ] Existing tests pass (verify via `pytest`)
- [ ] No new patient creation regression when name is unique
