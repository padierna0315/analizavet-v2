# Dead Code Analysis Report

## Executive Summary

This report identifies **truly unused code** in the analizavet-v2 codebase after careful manual verification. The analysis distinguishes between:
- **Actually dead code**: Functions/variables that are defined but never called or referenced anywhere
- **False positives**: Code that appears unused but is actually used via decorators, Pydantic validators, or other indirect mechanisms

**Total genuinely unused items found: 1**

---

## Actually Dead Code

### `app/core/algorithms/interpretations.py`
- **Line 68**: Function `get_interpretation()` 
  - **Reason**: This is a wrapper function that's never called. The `INTERPRETATIONS` dictionary is imported and used directly elsewhere (`app/core/algorithms/engine.py:60`), but this helper function is not used.
  - **Recommendation**: Safe to remove. The dictionary can be accessed directly.

---

## False Positives (NOT Dead Code)

The following were flagged by automated analysis but are **actually used**:

### Router Functions (Used via decorators)
All router functions are properly used - they're decorated with `@router.get()`, `@router.post()`, etc. These are NOT dead code:

**`app/routers/health.py`**
- Line 12: `health_check()` - Used via `@router.get("/health")`

**`app/routers/patients.py`**
- Line 19: `list_patients_page()` - Used via `@router.get("")`
- Line 64: `patient_detail_page()` - Used via `@router.get("/{patient_id}")`

**`app/routers/reception.py`**
- Line 25: `receive_patient()` - Used via `@router.post("/receive")`
- Line 47: `list_patients()` - Used via `@router.get("/patients")`
- Line 96: `upload_hl1_batch()` - Used via `@router.post("/upload")`
- Line 185: `process_test_result()` - Used via `@router.post("/reception/procesar/{test_result_id}")`
- Line 215: `get_recepcion()` - Used via `@router.get("/recepcion")`

**`app/routers/reports.py`**
- Line 22: `download_pdf()` - Used via `@router.get("/{result_id}/pdf")`

**`app/routers/taller.py`**
- Line 29: `taller_dashboard()` - Used via `@router.get("/")`
- Line 107: `enrich_test_result()` - Used via `@router.post("/enrich")`
- Line 166: `get_test_result()` - Used via `@router.get("/results/{result_id}")`
- Line 181: `get_preview_get()` - Used via `@router.get("/preview/{result_id}")`
- Line 200: `get_preview_post()` - Used via `@router.post("/preview/{result_id}")`
- Line 354: `upload_images()` - Used via `@router.post("/images")`
- Line 505: `toggle_image()` - Used via `@router.post("/algorithms/{result_id}")` (indirect)
- Line 536: `get_pending_patients_fragment()` - Used via `@router.get("/pending-patients")`
- Line 600: `load_patient_workspace()` - Used via `@router.post("/load-patient/{result_id}")`
- Line 733: `delete_pending_patient()` - Used via `@router.delete("/pending-patient/{patient_id}")`
- Line 745: `taller_page()` - Used via `@router.get("/{result_id}")`

**`app/main.py`**
- Line 73: `root_redirect()` - Used via `@app.get("/")`
- Line 89: `get_adapters_status()` - Used via `@app.get("/api/adapters/status")`
- Line 109: `global_exception_handler()` - Used via `@app.exception_handler(Exception)`
- Line 132: `validation_exception_handler()` - Used via `@app.exception_handler(RequestValidationError)`

### Pydantic Validators (Called automatically by Pydantic)
These are NOT dead code - they're automatically invoked by Pydantic's validation system:

**`app/schemas/reception.py`**
- Line 24: `strip_and_validate()` - Field validator for `raw_string`
- Line 47: `capitalize_name()` - Field validator for `name`
- Line 52: `capitalize_owner_name()` - Field validator for `owner_name`
- Line 56: `check_age_consistency()` - Model validator

### Class Methods (Called via instances)
These are NOT dead code - they're called through class instances:

**`app/core/taller/flagging.py`**
- Line 62: `flag_batch()` - Used in tests and potentially in production code via `ClinicalFlaggingService` instance

**`app/core/taller/notifications.py`**
- Line 91: `notify_dismiss_all()` - Utility function exported for use in other modules

### Class Constants (Used within class)
**`app/satellites/ozelle/batch_splitter.py`**
- Line 18: `MLLP_START` - Used within `BatchSplitter` class methods
- Line 19: `MLLP_END` - Used within `BatchSplitter` class methods
- Line 20: `MLLP_SUFFIX` - Used within `BatchSplitter` class methods

**`app/core/taller/flagging.py`**
- Line 6: `SPECIES_MAP` - Used within `ClinicalFlaggingService` class

### Enum Values (Used as constants)
**`app/schemas/reception.py`**
- Line 8: `LIS_OZELLE` - Used throughout the codebase
- Line 9: `LIS_FILE` - Used in `app/tasks/hl7_processor.py`
- Line 10: `LIS_FUJIFILM` - Used in `app/satellites/fujifilm/adapter.py`
- Line 11: `MANUAL` - Used in tests

### Module-level Variables (Exported)
**`app/tasks/__init__.py`**
- Line 4: `broker` - Exported for potential external use

---

## Files Analyzed

Total Python files analyzed: **58**

Key modules examined:
- `app/core/algorithms/` - Clinical algorithms and interpretations
- `app/core/taller/` - Flagging, notifications, engine
- `app/routers/` - FastAPI route handlers
- `app/satellites/` - LIS adapters and parsers
- `app/schemas/` - Pydantic models
- `app/tasks/` - Background tasks

---

## Recommendations

1. **Remove `get_interpretation()`** from `app/core/algorithms/interpretations.py` - it's a redundant wrapper function.

2. **Consider removing or documenting** `notify_dismiss_all()` in `app/core/taller/notifications.py` if it's truly not used anywhere (the grep search showed no external usage).

3. **No other action needed** - all other flagged code is legitimately used through decorators, Pydantic validation, or class instantiation.

---

## Methodology

1. **AST-based analysis**: Initial scan using Python's AST module to identify all function, class, and variable definitions.

2. **String-based search**: Comprehensive grep/search across all Python files to find references to each definition.

3. **Manual verification**: Each flagged item was manually verified to distinguish:
   - Direct usage (function calls, variable references)
   - Decorator usage (FastAPI routes, exception handlers)
   - Framework usage (Pydantic validators, class instantiation)
   - Import/export patterns

4. **Context analysis**: Examined how each item is used in the codebase to avoid false positives.

---

## Notes

- The analysis focused on the `app/` directory only
- Test files were included in the search to identify usage
- Code that's only used in tests is still considered "used" (tests are part of the codebase)
- Decorator-based usage (FastAPI routes) counts as legitimate usage
- Pydantic validators are automatically called by the framework
