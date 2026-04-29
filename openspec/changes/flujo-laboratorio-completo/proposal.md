# Proposal: Complete Laboratory Flow Implementation

## Intent

Implement a complete end-to-end laboratory results processing workflow that allows uploading HL7 batch files via web interface and automatically processing them through parsing, normalization, deduplication, and image handling to generate final reports with extracted images.

## Scope

### In Scope
- Implement web-based HL7 batch file upload functionality
- Process HL7 batch files with multiple patients
- Extract images from HL7 OBX|ED segments
- Auto-triage images for PDF inclusion
- Generate final reports with included images

### Out of Scope
- Manual image selection interface
- Manual processing steps
- Storing original .txt files
- Real-time processing (existing TCP/MLLP server remains primary method)

## Capabilities

### New Capabilities
- `hl7-batch-upload`: Web-based upload of HL7 batch files with automatic processing
- `image-auto-triage`: Automatic image selection for report generation
- `hl7-batch-processing`: Complete processing pipeline for uploaded HL7 batch files

### Modified Capabilities
- None

## Approach

1. Add web upload endpoint at `POST /reception/upload` to handle HL7 batch files
2. Parse, normalize, deduplicate, and store all patient data from uploaded files
3. Extract images from Base64 segments in OBX|ED
4. Auto-triage images for PDF report generation
5. Generate PDF reports with auto-selected images

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/routers/reception.py` | New | Add file upload endpoint |
| `app/core/reception/` | Modified | Add batch processing logic |
| `app/core/taller/` | Modified | Add image extraction and auto-triage logic |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Performance issues with large batch files | Medium | Implement async processing with progress indication |
| File upload security concerns | Medium | Validate file format and implement size limits |
| Image processing failures | Medium | Add comprehensive error handling and logging |
| Database storage issues with large images | Low | Optimize image storage and retrieval mechanisms |

## Rollback Plan

If this feature causes issues, we can rollback by removing the new endpoints and reverting to TCP/MLLP only processing.

## Dependencies

- Existing HL7 parser in `app/satellites/ozelle/hl7_parser.py`
- Existing image extraction in `app/core/taller/images.py`
- Existing PDF generation in `app/core/reports/service.py`

## Success Criteria

- [x] HL7 batch file upload endpoint implemented
- [x] Batch processing pipeline working
- [x] Images properly extracted from HL7 segments
- [x] Auto-triage for image selection working
- [x] PDF generation with images working
- [ ] All checkpoints verified by Santiago