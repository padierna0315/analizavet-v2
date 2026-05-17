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

- [ ] 1.1 `app/domains/reception/service.py` (~line 105): Change `lookup_code = raw_input.session_code or raw_input.raw_string` to `lookup_code = raw_input.session_code` — fallback to `raw_string` MUST NOT serve as session_code lookup
- [ ] 1.2 `app/domains/reception/service.py` (Fujifilm block, ~lines 184-187): Replace `result.scalars().first()` with `result.scalars().all()` + `len(matches) == 1` guard — create new patient when 0 or 2+ patients share the normalized name
- [ ] 1.3 `app/domains/reception/service.py` (Ozelle/File block, ~lines 246-249): Same `.all()` + `len(matches) == 1` guard as Fujifilm

## Phase 2: Update and Add Unit Tests

- [ ] 2.1 `tests/unit/test_reception_service.py`: Update mock helpers and existing Ozelle/Fujifilm match tests — replace `scalars().first()` mocks with `scalars().all()` returning a list of matches (empty list for no match, single-element list for one match)
- [ ] 2.2 Add Fujifilm tests for 0, 1, and 2+ name matches: 0 matches → fallthrough to `_find_existing`; 1 match → reuse patient (`created=False`); 2+ matches → create new patient (`created=True`)
- [ ] 2.3 Add Ozelle tests for 0, 1, and 2+ name matches: same three scenarios (0 fallthough to `_find_existing`, 1 reuse, 2+ create new)
- [ ] 2.4 Add File source tests (same scenarios as Ozelle, confirmed it follows the Ozelle/File path)
- [ ] 2.5 Add test for `raw_string` no longer serving as `session_code` fallback: verify that when `session_code` is `None` and `raw_string` happens to match another patient's `session_code`, the system proceeds to name-based fallback instead of matching by code
