import requests, pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path("data")
OUT.mkdir(exist_ok=True)

def fetch(name, start, end, extra=None, step_days=2):
    rows, t = [], start
    while t < end:
        t2 = min(t + timedelta(days=step_days), end)
        params = {
            "publishDateTimeFrom": t.strftime("%Y-%m-%dT%H:%MZ"),
            "publishDateTimeTo": t2.strftime("%Y-%m-%dT%H:%MZ"),
            **(extra or {}),
        }
        r = requests.get(f"{BASE}/{name}/stream", params=params, timeout=120)
        r.raise_for_status()
        data = r.json()
        rows += data["data"] if isinstance(data, dict) else data
        print(name, t.date(), "->", t2.date(), "total rows:", len(rows))
        t = t2
    return pd.DataFrame(rows).drop_duplicates()

utc = timezone.utc
actuals = fetch("FUELHH", datetime(2026, 1, 2, tzinfo=utc),
                datetime(2026, 2, 3, tzinfo=utc), {"fuelType": "WIND"})
forecasts = fetch("WINDFOR", datetime(2025, 12, 30, tzinfo=utc),
                  datetime(2026, 2, 1, tzinfo=utc))

actuals.to_csv(OUT / "actuals.csv", index=False)
forecasts.to_csv(OUT / "forecasts.csv", index=False)

fc = forecasts.copy()
fc["startTime"] = pd.to_datetime(fc["startTime"], utc=True)
fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True)
ac = actuals.copy()
ac["startTime"] = pd.to_datetime(ac["startTime"], utc=True)

print("\nACTUALS rows:", len(ac), "| start:", ac.startTime.min(), "| end:", ac.startTime.max())
print("FORECAST rows:", len(fc))
print("Forecast startTime minutes:\n", fc.startTime.dt.minute.value_counts())
print("Forecasts per startTime:\n", fc.groupby("startTime").size().describe())
print("Horizon hours (startTime - publishTime):\n",
      ((fc.startTime - fc.publishTime).dt.total_seconds() / 3600).describe())
print("Publish minutes:\n", fc.publishTime.dt.minute.value_counts())