# Specification for image-auto-triage

## Purpose

This specification defines the requirements for automatic image selection and handling in the HL7 processing pipeline.

## Requirements

### Requirement: Image Extraction
The system MUST extract images from Base64 segments in OBX|ED sections of HL7 messages.

The system MUST handle corrupted image data gracefully without stopping the overall processing pipeline.

#### Scenario: Successful image extraction
- GIVEN an HL7 message with valid Base64 image data
- WHEN the system processes the message
- THEN it MUST extract and store the images correctly

#### Scenario: Corrupted image data
- GIVEN an HL7 message with corrupted Base64 image data
- WHEN the system processes the message
- THEN it MUST log the error and skip image processing while continuing with other processing

### Requirement: Auto-Triage for Report Generation
The system MUST automatically triage which images to include in reports based on the existing auto-triage logic.

The system MUST select images for inclusion in the final PDF report without user intervention.

#### Scenario: Auto-triage working correctly
- GIVEN multiple images extracted from an HL7 message
- WHEN the system applies auto-triage logic
- THEN it MUST correctly select the appropriate images for the report

#### Scenario: No images to process
- GIVEN an HL7 message with no images
- WHEN the system processes the message
- THEN the auto-triage process MUST complete without error