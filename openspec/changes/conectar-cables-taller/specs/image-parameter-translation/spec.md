# Image Parameter Translation Specification

## Purpose

This spec defines the requirements for translating image parameter codes in the taller module, ensuring all necessary codes are properly handled.

## ADDED Requirements

### Requirement: Image Parameter Code Translation

The system MUST handle the following image parameter codes in IMAGE_PARAMETER_TRANSLATION:
- Composite codes with `/` such as `NST/WBC`, `NST/NEU`, `NSH/WBC`, `NSH/NEU`
- Simple codes: `MPV`, `PDW`, `PCT`
- The system SHALL map these codes to appropriate Spanish names for display

#### Scenario: All required image parameter codes are supported

- GIVEN the system processes image parameter codes
- WHEN the IMAGE_PARAMETER_TRANSLATION is checked for required codes
- THEN all required codes (`NST/WBC`, `NST/NEU`, `NSH/WBC`, `NSH/NEU`, `MPV`, `PDW`, `PCT`) are found in the translation table

#### Scenario: Image parameter codes are correctly translated

- GIVEN an image parameter code from a supported instrument
- WHEN the system translates the code using IMAGE_PARAMETER_TRANSLATION
- THEN the system returns the correct Spanish name for the parameter

## MODIFIED Requirements

### Requirement: Image Parameter Processing

The system SHALL process image parameters including the new codes (`NST/WBC`, `NST/NEU`, `NSH/WBC`, `NSH/NEU`, `MPV`, `PDW`, `P-CRIT`)
(Previously: The system did not handle missing image parameter codes)

#### Scenario: Process hemogram parameters from Ozelle instrument

- GIVEN an Ozelle instrument sends hemogram parameters including `NST/WBC`, `NST/NEU`, `NSH/WBC`, `NSH/NEU`, `MPV`, `PDW`, `PCT`
- WHEN the system processes these parameters
- THEN no warnings of "Código de imagen desconocido" are displayed for these parameters