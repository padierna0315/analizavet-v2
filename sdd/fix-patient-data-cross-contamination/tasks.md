# Tasks: Fix Patient Data Cross-Contamination

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 50–80 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | exception-ok |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Fix service.py + update tests | PR 1 | Single PR, base = main |

## Phase 1: Fix Service Logic

- [x] 1.1 `app/domains/reception/service.py` (~line 105): Changed `lookup_code = raw_input.session_code or raw_input.raw_string` to `lookup_code = raw_input.session_code` — guarded with `if lookup_code:`. Fallback to `raw_string` MUST NOT serve as session_code lookup.
- [x] 1.2 `app/domains/reception/service.py` (Fujifilm block, ~lines 192-195): Replaced `result.scalars().first()` with `result.scalars().all()` + `if len(fuji_matches) == 1` guard — create new patient when 0 or 2+ patients share the normalized name.
- [x] 1.3 `app/domains/reception/service.py` (Ozelle/File block, ~lines 256-259): Same `.all()` + `len(ozelle_matches) == 1` guard as Fujifilm.

## Phase 2: Update and Add Unit Tests

- [x] 2.1 `tests/unit/test_reception_service.py`: Updated mock helpers and existing Ozelle/Fujifilm match tests — replaced `scalars().first()` mocks with `scalars().all()` returning a list of matches (empty list for no match, single-element list for one match).
- [x] 2.2 Added Fujifilm tests for 0, 1, and 2+ name matches: 0 matches → fallthrough to `_find_existing` or creation; 1 match → reuse patient (`created=False`); 2+ matches → create new patient (`created=True`).
- [x] 2.3 Added Ozelle tests for 0, 1, and 2+ name matches: same three scenarios (0 fallthrough, 1 reuse, 2+ create new).
- [x] 2.4 Added File source tests (same scenarios as Ozelle, confirmed it follows the Ozelle/File path).
- [x] 2.5 Added test for `raw_string` no longer serving as `session_code` fallback: verified that when `session_code` is `None`, execute is called exactly once (only name query, no session_code lookup with raw_string).
