# Configuration Files

...existing content...

config.yaml:
Contains structured configuration for your server, Twilio, SMTP, cloud storage, and sensor settings. Placeholders (e.g., ${TWILIO_ACCOUNT_SID}) are used for secrets that will be loaded from environment variables.

config.py:
Uses python-dotenv to load the .env file and PyYAML to read the YAML file. It includes a helper function to recursively replace placeholder strings with their corresponding environment variable values.

.env File:
This file holds sensitive credentials and should not be committed to version control.