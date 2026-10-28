import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"
CUTOFF_HOUR = 9  # decision time on D-1, UTC (same as UK time in January)
WINDOW_START = pd.Timestamp("2026-01-02", tz="UTC")  # first delivery day
WINDOW_END = pd.Timestamp("2026-02-02", tz="UTC")    # exclusive


def load():
    ac = pd.read_csv(DATA / "actuals.csv")
    fc = pd.read_csv(DATA / "forecasts.csv")
    ac["startTime"] = pd.to_datetime(ac["startTime"], utc=True)
    fc["startTime"] = pd.to_datetime(fc["startTime"], utc=True)
    fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True)
    ac = (ac[["startTime", "generation"]]
          .rename(columns={"generation": "actual"})
          .drop_duplicates("startTime"))
    return ac, fc


def latest_forecasts(fc, cutoff_hour=CUTOFF_HOUR):
    """For each target hour, the latest forecast published at or before
    the day-ahead decision time (cutoff_hour on the day before delivery)."""
    fc = fc.copy()
    delivery_day = fc["startTime"].dt.normalize()
    fc["cutoff"] = delivery_day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)
    ok = fc[fc["publishTime"] <= fc["cutoff"]]
    latest = ok.sort_values("publishTime").groupby("startTime", as_index=False).last()
    return latest[["startTime", "publishTime", "generation", "cutoff"]].rename(
        columns={"generation": "forecast"})


def compare(ac, fc, cutoff_hour=CUTOFF_HOUR):
    df = latest_forecasts(fc, cutoff_hour).merge(ac, on="startTime", how="inner")
    df = df[(df["startTime"] >= WINDOW_START) & (df["startTime"] < WINDOW_END)].copy()
    df["error"] = df["forecast"] - df["actual"]  # positive = over-forecast
    return df


def metrics(df):
    e = df["error"]
    return {
        "n": int(len(e)),
        "mae": float(e.abs().mean()),
        "rmse": float((e ** 2).mean() ** 0.5),
        "bias": float(e.mean()),
    }