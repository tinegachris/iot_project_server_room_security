# Server-side Integration/Unit Tests

...existing content...
Testing
Server tests (tests/test_main.py, tests/test_routes.py) and integration tests (tests/integration/):
– Create or update tests to verify the new API endpoints and ensure the end-to-end flow works as expected.
– Write unit tests for any new sensor handling or business logic added in the controllers.

test_main.py:

Calls the /api/status endpoint and confirms that the returned JSON includes a status of "normal" and a timestamp.
test_routes.py:

test_trigger_alert: Posts an alert payload and expects a 201 status code, with a JSON response confirming the alert was processed (including a log_id).
test_manual_control_valid: Verifies that sending valid control commands ("lock" and "unlock") returns a 200 status code with an appropriate success message.
test_manual_control_invalid: Ensures that sending an invalid command returns a 400 error with a detail message.