# Specification for hl7-batch-processing

## Purpose

This specification defines the requirements for processing HL7 batch files through the automated pipeline.

## Requirements

### Requirement: Batch Splitter
The system MUST split HL7 batch files into individual messages using MLLP framing characters or MSH segments.

The system MUST filter out HEARTBEAT messages (MSH-9 = ZHB^H00) silently during processing.

#### Scenario: Processing batch with valid messages and heartbeats
- GIVEN an HL7 batch file containing both valid ORU^R01 messages and HEARTBEAT messages
- WHEN the system processes the batch
- THEN it MUST process only the valid messages and ignore HEARTBEAT messages

#### Scenario: Batch with only valid messages
- GIVEN an HL7 batch file containing only valid ORU^R01 messages
- WHEN the system processes the batch
- THEN it MUST process all messages successfully

#### Scenario: Batch with only heartbeats
- GIVEN an HL7 batch file containing only HEARTBEAT messages
- WHEN the system processes the batch
- THEN it MUST ignore all messages and report zero valid results

### Requirement: Auto-Processing Pipeline
The system MUST process each HL7 message through the complete pipeline including parsing, normalization, deduplication, and image handling.

The system MUST create or link patient records as needed.

The system MUST apply auto-triage to select images for reports.

#### Scenario: Processing patient with valid data
- GIVEN an HL7 message with valid patient data
- WHEN the system processes the message
- THEN it MUST create or link the patient record and store test results

#### Scenario: Processing duplicate patient
- GIVEN an HL7 message with patient data that already exists
- WHEN the system processes the message
- THEN it MUST link to the existing patient record rather than creating a new one

#### Scenario: Image extraction failure
- GIVEN an HL7 message with corrupted Base64 image data
- WHEN the system processes the message
- THEN it MUST log the error and continue processing other parts of the message

### Requirement: Reception Queue
The system MUST display pending patients in the reception queue for the last 24 hours.

The system MUST provide HTMX auto-refresh every 30 seconds.

#### Scenario: Viewing pending patients
- GIVEN patients have been uploaded and are pending processing
- WHEN a user accesses the reception page
- THEN the system MUST display all patients with status "pendiente" from the last 24 hours

#### Scenario: Auto-refresh of reception queue
- GIVEN patients are being processed
- WHEN the user is on the reception page
- THEN the page MUST automatically refresh every 30 seconds to show updated status