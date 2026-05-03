# Specifications for instrument-logfire Change

## Functional Requirements

### Primary Goal
Implement Logfire observability in Analizavet-v2 to provide visibility into application behavior, particularly Pydantic validation failures and other runtime events.

### Key Functional Requirements

1. **Logfire Configuration**
   - Configure Logfire to capture application events and errors
   - Integrate with FastAPI to automatically capture HTTP requests and responses
   - Capture Pydantic validation errors and display them in the Logfire dashboard

2. **Pydantic Validation Visibility**
   - Capture and display validation errors from Pydantic models in the Logfire dashboard
   - Show which fields failed validation and why
   - Provide clear error messages for debugging purposes

3. **Error Tracking**
   - Track application exceptions and display them in the Logfire dashboard
   - Capture request/response information for debugging
   - Show performance metrics for API endpoints

## Non-Functional Requirements

1. **Performance**
   - Minimal performance impact on application execution
   - Non-blocking instrumentation that doesn't slow down request processing

2. **Security**
   - No sensitive data should be logged (PII filtering if needed)
   - Follow security best practices for observability tools

3. **Usability**
   - Clear visualization of errors in the Logfire dashboard
   - Easy identification of validation failures
   - Intuitive error messages for debugging

## Detailed Scenarios (Acceptance Criteria)

### Scenario 1: Pydantic Validation Error Visibility
**Given** a user submits invalid patient data through the API
**When** the Pydantic validation fails
**Then** the validation error should be visible in the Logfire dashboard with:
- Field name that failed validation
- Reason for validation failure
- The value that caused the failure
- HTTP endpoint where the error occurred

### Scenario 2: Successful Logfire Configuration
**Given** the application is running with Logfire instrumentation
**When** a request is made to any endpoint
**Then** the request should appear in the Logfire dashboard with:
- Request method and URL
- Response status code
- Request duration
- Any errors that occurred

### Scenario 3: Exception Tracking
**Given** an unexpected error occurs in the application
**When** the error is logged
**Then** it should appear in the Logfire dashboard with:
- Error type and message
- Stack trace
- Request context (if applicable)

## Affected Files

### Primary Files to Modify
1. `app/main.py` - Add Logfire configuration and instrumentation
2. `app/core/**` - Pydantic models that will emit validation events to Logfire

### Files to Review
1. `app/logging_config.py` - May need to be updated or replaced with Logfire
2. `app/schemas/reception.py` - Contains Pydantic models with validation

## Integration Points

### FastAPI Integration
- Use `logfire.instrument_fastapi(app)` to automatically instrument FastAPI endpoints
- This will capture HTTP requests, responses, and exceptions automatically

### Pydantic Integration
- Pydantic validation errors will automatically be captured by Logfire when integrated with FastAPI
- Custom validation logic in models will emit events to Logfire

### Application Lifecycle
- Logfire configuration will be added to `app/main.py` during application startup
- Configuration will include instrumenting the FastAPI app for automatic observability

## Implementation Approach

1. Add Logfire configuration to `app/main.py`
2. Replace or supplement existing `loguru` logging with Logfire where appropriate
3. Ensure Pydantic validation errors are captured and displayed in the Logfire dashboard
4. Verify instrumentation by testing validation failures and checking the Logfire dashboard

## Verification Steps

1. Start the application with Logfire instrumentation
2. Access the Logfire dashboard (typically at http://localhost:4000 or similar)
3. Trigger a Pydantic validation error by submitting invalid data to an endpoint
4. Observe that the validation error appears in the Logfire dashboard with details
5. Verify that normal requests also appear in the dashboard with timing and status information