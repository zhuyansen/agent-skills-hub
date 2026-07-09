"""Generate an ADC-format credential for analytics-mcp — no gcloud SDK needed.

Reuses the GSC desktop OAuth client (same Cloud project). Opens a browser for
consent on the analytics scopes, then writes ops/ga/adc.json in the exact
format `gcloud auth application-default login` would produce.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(HERE, "..", "gsc", "credentials.json")
OUT = os.path.join(HERE, "adc.json")
SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/cloud-platform",
]

flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
creds = flow.run_local_server(port=0)
client = json.load(open(CLIENT))["installed"]
adc = {
    "client_id": client["client_id"],
    "client_secret": client["client_secret"],
    "refresh_token": creds.refresh_token,
    "quota_project_id": client["project_id"],
    "type": "authorized_user",
}
with open(OUT, "w") as f:
    json.dump(adc, f, indent=1)
print(f"✓ ADC written: {OUT} (project: {client['project_id']})")
