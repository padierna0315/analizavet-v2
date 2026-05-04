# Taller PDF Generation Specification

## Purpose

This spec defines the requirements for PDF generation functionality in the taller module, ensuring the PDF button works correctly with the appropriate result_id and generates valid PDF reports.

## ADDED Requirements

### Requirement: PDF Button Functionality

The system MUST display a "Generar PDF" button in the taller dashboard that:
- Is hidden or disabled when no patient is loaded in the workspace
- Becomes visible and functional when a patient is loaded
- Correctly passes the result_id to generate a patient-specific PDF
- Opens the PDF in a new tab when clicked

#### Scenario: User loads a patient and clicks the PDF button

- GIVEN a user has loaded a patient in the taller workspace
- WHEN the user clicks the "Generar PDF" button
- THEN the system generates a PDF for the loaded patient and opens it in a new tab

#### Scenario: No patient is loaded in the workspace

- GIVEN no patient is loaded in the taller workspace
- WHEN the user views the dashboard
- THEN the "Generar PDF" button is hidden or disabled

## MODIFIED Requirements

### Requirement: Dashboard HTML Generation

The system SHALL generate workspace HTML that includes the correct result_id for PDF generation.
(Previously: The PDF button on the dashboard does not have the correct result_id to generate reports)

#### Scenario: Workspace HTML includes correct result_id

- GIVEN a patient is loaded in the taller workspace
- WHEN the system generates the workspace HTML
- THEN the HTML includes the correct result_id for PDF generation

## ADDED Requirements

### Requirement: PDF Generation Endpoint

The system MUST provide a valid PDF when the endpoint `/reports/{result_id}/pdf` is called with status 200 and content-type application/pdf.