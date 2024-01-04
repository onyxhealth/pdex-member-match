# settings.py
# Global settings
import os
from icecream import ic

DEFAULT_DESCRIPTION = "unprocessable entity"
DEFAULT_STATUS_CODE = 422
DEFAULT_SEVERITY = "error"
DEFAULT_CODE = "processing"
REQUIRED_PARAMETERS = ["MemberPatient", "CoverageToMatch", "Consent"]
DEFAULT_PORT = 8000
# FHIR_BASE_URL = "http://localhost:8080/fhir"
# DEFAULT_FHIR_STORE = "localhost:8080/fhir"
DEFAULT_SECURE = "http://"
DEFAULT_FHIR_STORE = "localhost"
DEFAULT_FHIR_STORE_PORT = "8080"
DEFAULT_FHIR_STORE_PATH = "/fhir"

FHIR_BASE_URL = os.getenv('FHIR_STORE_HTTP', DEFAULT_SECURE) + os.getenv('FHIR_STORE_SERVER', DEFAULT_FHIR_STORE) + \
                ":" + os.getenv('FHIR_STORE_PORT', DEFAULT_FHIR_STORE_PORT) + \
                os.getenv('FHIR_STORE_PATH', DEFAULT_FHIR_STORE_PATH)
# FHIR_BASE_URL = "http://172.17.0.2:8080/fhir"
ic(FHIR_BASE_URL)
ic("DEFAULT_PORT={DEFAULT_PORT}")
FHIR_BASE_URI = FHIR_BASE_URL

SECURE_URL = False   # True
TENANT = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
AUTH_URL = ""

# Values = "EXCLUDED" | "INCLUDED_LABELLED" | "INCLUDED_NOLABEL"
FHIR_STORE_SENSITIVITY = "EXCLUDED"

