"""Quick test to verify JSearch API key works.

Usage (from backend/ with venv active):
  set RAPIDAPI_KEY=your_key   # PowerShell: $env:RAPIDAPI_KEY="..."
  python test_jsearch.py
"""
import os
import sys

import httpx

KEY = os.getenv("RAPIDAPI_KEY", "").strip()
if not KEY:
    print("Set RAPIDAPI_KEY in the environment (or backend/.env) before running.")
    sys.exit(1)

resp = httpx.get(
    "https://jsearch.p.rapidapi.com/search",
    headers={
        "X-RapidAPI-Key": KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    },
    params={"query": "software developer Bangladesh", "page": "1", "num_pages": "1"},
    timeout=30,
)

print(f"Status: {resp.status_code}")
data = resp.json()
jobs = data.get("data") or []

if jobs:
    print(f"SUCCESS! Found {len(jobs)} jobs:")
    for j in jobs[:5]:
        print(f"  - {j.get('job_title')} @ {j.get('employer_name')} ({j.get('job_city', 'N/A')})")
else:
    print(f"Response: {data}")
    print()
    print("If you see 'not subscribed', go to:")
    print("  https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/pricing")
    print("  Click 'Subscribe' on the Basic (FREE) plan, then re-run this script.")
