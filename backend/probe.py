import requests, json

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
P = {"publishDateTimeFrom": "2026-01-10T00:00Z",
     "publishDateTimeTo": "2026-01-12T00:00Z"}

def probe(name, extra=None):
    r = requests.get(f"{BASE}/{name}/stream", params={**P, **(extra or {})}, timeout=60)
    print("\n==", name, r.status_code, r.url)
    try:
        data = r.json()
    except Exception:
        print(r.text[:500]); return
    rows = data["data"] if isinstance(data, dict) and "data" in data else data
    if isinstance(rows, list):
        print("rows:", len(rows))
        for row in rows[:5]:
            print(json.dumps(row))
    else:
        print(json.dumps(data)[:800])

probe("FUELHH", {"fuelType": "WIND"})
probe("WINDFOR")