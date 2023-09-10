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
DEFAULT_FHIR_STORE = "https://hapisever.azurewebsites.net"
#DEFAULT_FHIR_STORE = "https://c783-64-152-236-98.ngrok.io"
DEFAULT_FHIR_STORE_PORT = "8080"

FHIR_BASE_URL = os.getenv('FHIR_STORE_SERVER', DEFAULT_FHIR_STORE)
# FHIR_BASE_URL = "http://172.17.0.2:8080/fhir"
ic(FHIR_BASE_URL)
FHIR_BASE_URI = FHIR_BASE_URL

SECURE_URL = False   # True
TENANT = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
AUTH_URL = ""

# Values = "EXCLUDED" | "INCLUDED_LABELLED" | "INCLUDED_NOLABEL"
FHIR_STORE_SENSITIVITY = "INCLUDED_NOLABEL"

