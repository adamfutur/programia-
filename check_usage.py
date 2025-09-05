import requests
import os
import json

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

base_url = OPENAI_API_BASE.replace('/v1', '') if OPENAI_API_BASE else ''
url = f"{base_url}/key/info"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}

response = requests.get(url, headers=headers)
response = response.json()
utilization = {
    "tpm_limit": response.get('info', {}).get('tpm_limit'),
    "rpm_limit": response.get('info', {}).get('rpm_limit'),
    "max_budget": response.get('info', {}).get('max_budget'),
    "budget_utilised": response.get('info', {}).get('spend'),
    "remaining_budget": response.get('info', {}).get('max_budget') - response.get('info', {}).get('spend', 0) if response.get('info', {}).get('max_budget') is not None else None
}
print(json.dumps(utilization, indent=2))