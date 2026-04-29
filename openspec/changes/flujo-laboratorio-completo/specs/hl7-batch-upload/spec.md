# Delta for hl7-batch-upload

## ADDED Requirements

### Requirement: Web-based HL7 Batch File Upload
The system MUST provide a web-based file upload endpoint that accepts HL7 batch files in .txt format and processes them through an automated pipeline.

The system MUST validate the file type and reject any file that is not a .txt file with an appropriate error message.

The system MUST process files asynchronously using Dramatiq background workers.

The system MUST return an immediate HTML redirect response to the reception page after upload.

#### Scenario: Successful batch file upload
- GIVEN a user wants to upload an HL7 batch file
- WHEN they access the upload form and submit a valid .txt file
- THEN the system MUST accept the file and start processing it in the background

#### Scenario: Invalid file type upload
- GIVEN a user attempts to upload a file that is not .txt
- WHEN the system validates the file type
- THEN it MUST reject the file with a clear error message

#### Scenario: File upload with progress indication
- GIVEN a user is uploading a large HL7 batch file
- WHEN the system is processing the file
- THEN the system MUST show progress indicators to the user

### Requirement: Batch File Processing
The system MUST parse the HL7 batch file, extract patient data, and process images automatically.

The system MUST handle errors gracefully and provide appropriate feedback to users.

#### Scenario: Happy path - Upload valid batch file
- GIVEN a valid HL7 batch file is uploaded
- WHEN the file is processed through the pipeline
- THEN patient data and images are extracted and stored correctly

#### Scenario: Large batch processing with progress indication
- GIVEN a large HL7 batch file
- WHEN the system processes the file
- THEN it MUST show progress indicators to the user

## MODIFIED Requirements

### Requirement: File Upload Endpoint
The system MUST provide a secure file upload mechanism for HL7 batch files with appropriate validation and security measures.

The system MUST handle file uploads via a web form on the existing dashboard.

The system MUST validate file size does not exceed 10MB (configurable via Dynaconf).

#### Scenario: User uploads valid HL7 batch file
- GIVEN a valid HL7 batch file
- WHEN the user submits the file via the web form
- THEN the system MUST accept and process the file correctly

(Previously: The system had basic file upload capability through TCP/MLLP only)

#### Scenario: Invalid file type handling
- GIVEN a user uploads an invalid file type
- WHEN the system validates the file
- THEN it MUST reject invalid files with an appropriate error message

#### Scenario: File size validation
- GIVEN a user uploads a file larger than 10MB
- WHEN the system validates the file size
- THEN it MUST reject the file with an appropriate error message