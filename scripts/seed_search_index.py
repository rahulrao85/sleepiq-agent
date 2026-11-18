"""
Seed Azure AI Search Index with Sleep IQ medical knowledge.

Usage:
    python scripts/seed_search_index.py

Requires these .env vars:
    FOUNDRY_IQ_ENDPOINT, FOUNDRY_IQ_INDEX_NAME, FOUNDRY_IQ_API_KEY

Creates the index if it doesn't exist, then uploads all knowledge entries.
"""

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from foundry_iq import KNOWLEDGE_BASE
import requests


def create_index():
    """Create the search index via REST API."""
    endpoint = os.getenv('FOUNDRY_IQ_ENDPOINT').rstrip('/')
    index_name = os.getenv('FOUNDRY_IQ_INDEX_NAME', 'sleepiq-medical-knowledge')
    api_key = os.getenv('FOUNDRY_IQ_API_KEY')

    url = f"{endpoint}/indexes/{index_name}?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    body = {
        "name": index_name,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True},
            {"name": "source", "type": "Edm.String", "filterable": True, "searchable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "keywords", "type": "Collection(Edm.String)", "filterable": True, "searchable": True},
        ]
    }

    # Check if index exists
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        print(f'Index "{index_name}" already exists.')
        return

    # Create it
    resp = requests.put(url, headers=headers, json=body)
    if resp.status_code in (201, 204):
        print(f'Created index "{index_name}".')
    else:
        print(f'Failed to create index: {resp.status_code} {resp.text}')
        sys.exit(1)


def seed():
    endpoint = os.getenv('FOUNDRY_IQ_ENDPOINT', '').rstrip('/')
    index_name = os.getenv('FOUNDRY_IQ_INDEX_NAME', 'sleepiq-medical-knowledge')
    api_key = os.getenv('FOUNDRY_IQ_API_KEY')

    if not endpoint or not api_key:
        print('ERROR: Set FOUNDRY_IQ_ENDPOINT and FOUNDRY_IQ_API_KEY in .env')
        sys.exit(1)

    create_index()

    # Upload documents via REST API
    url = f"{endpoint}/indexes/{index_name}/docs/index?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    documents = []
    for entry in KNOWLEDGE_BASE:
        documents.append({
            "@search.action": "upload",
            "id": entry["id"],
            "source": entry["source"],
            "content": entry["content"],
            "keywords": entry["keywords"],
        })

    batch_size = 10
    total_succeeded = 0
    total_failed = 0

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        body = {"value": batch}
        resp = requests.post(url, headers=headers, json=body)
        result = resp.json()

        if resp.status_code == 200 or resp.status_code == 201:
            for item in result.get("value", []):
                if item.get("status", False):
                    total_succeeded += 1
                else:
                    total_failed += 1
                    print(f'  Failed: {item.get("key")}: {item.get("errorMessage")}')
        else:
            print(f'Upload batch failed: {resp.status_code} {resp.text}')
            total_failed += len(batch)

    print(f'Uploaded {total_succeeded}/{len(documents)} knowledge entries to "{index_name}".')
    if total_failed:
        print(f'Failed: {total_failed}')

    # Verify by search
    print("\nVerifying with test search...")
    search_url = f"{endpoint}/indexes/{index_name}/docs/search?api-version=2023-11-01"
    test_resp = requests.post(search_url, headers=headers, json={"search": "AHI classification", "top": 2})
    if test_resp.status_code == 200:
        results = test_resp.json()
        count = results.get("@odata.count", len(results.get("value", [])))
        print(f'Search works! Found {count} results for "AHI classification".')
        for r in results.get("value", []):
            print(f'  - [{r["id"]}] {r["source"]}')
    else:
        print(f'Search test failed: {test_resp.status_code} {test_resp.text}')


if __name__ == '__main__':
    seed()
