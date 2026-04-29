# Tasks: flujo-laboratorio-completo

## Phase 1: Foundation / Infrastructure

- [x] 1.1 Create `app/satellites/ozelle/batch_splitter.py` to handle splitting of HL7 batch files
- [x] 1.2 Add POST `/reception/upload` endpoint in `app/routers/reception.py` to accept file uploads
- [x] 1.3 Create `app/tasks/hl7_processor.py` with Dramatiq actor `process_uploaded_batch`

## Phase 2: Core Implementation

- [ ] 2.1 Implement batch splitting logic in `app/satellites/ozelle/batch_splitter.py` to parse MLLP-framed messages
- [ ] 2.2 Extend `app/routers/reception.py` with POST `/reception/upload` endpoint logic
- [ ] 2.3 Implement GET `/recepcion` in `app/routers/reception.py` and create template `app/templates/recepcion/index.html`
- [ ] 2.4 Modify `app/templates/taller/dashboard.html` to include the HL7 file upload form with HTMX attributes

## Phase 3: Integration / Wiring

- [ ] 3.1 Wire up the batch splitting with the existing HL7 parser in `app/satellites/ozelle/hl7_parser.py`
- [ ] 3.2 Connect batch splitting → HL7 parsing → normalizer → baul → DB creation → image extraction → triage in the Dramatiq pipeline
- [ ] 3.3 Ensure the upload endpoint correctly redirects to `/recepcion` after processing

## Phase 4: Testing

- [ ] 4.1 Write unit tests for `batch_splitter.py` covering normal and edge cases (e.g., files with only heartbeat messages)
- [ ] 4.2 Write integration tests for the full pipeline from upload to PDF generation
- [ ] 4.3 Add test for the new endpoint in `reception.py` ensuring it correctly handles file uploads and processes them
- [ ] 4.4 Test the new template rendering for `/recepcion` with auto-refresh via HTMX

## Phase 5: Cleanup / Documentation

- [ ] 5.1 Update any relevant documentation or comments to reflect the new batch processing feature
- [ ] 5.2 Remove any temporary code or files created during development