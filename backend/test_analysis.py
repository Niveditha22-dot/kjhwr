import pandas as pd
from analysis import latest_forecasts, metrics


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def test_picks_latest_forecast_before_cutoff():
    fc = pd.DataFrame({
        "startTime": [ts("2026-01-05 12:00")] * 4,
        "publishTime": [ts("2026-01-03 08:30"), ts("2026-01-04 08:30"),
                        ts("2026-01-04 09:30"), ts("2026-01-05 13:30")],
        "generation": [50, 100, 200, 300],
    })
    out = latest_forecasts(fc, cutoff_hour=9)
    assert len(out) == 1
    assert out.iloc[0]["forecast"] == 100  # ignores the 09:30 and post-hoc ones


def test_metrics():
    m = metrics(pd.DataFrame({"error": [10, -10]}))
    assert m["mae"] == 10 and m["rmse"] == 10 and m["bias"] == 0