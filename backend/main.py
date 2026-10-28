import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from analysis import load, compare, metrics, CUTOFF_HOUR

app = FastAPI(title="Wind forecast API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET"], allow_headers=["*"])

AC, FC = load()


def frame(cutoff_hour):
    return compare(AC, FC, cutoff_hour)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/series")
def series(cutoff_hour: int = Query(CUTOFF_HOUR, ge=0, le=23), day: str | None = None):
    df = frame(cutoff_hour)
    if day:
        d = pd.Timestamp(day, tz="UTC")
        df = df[(df["startTime"] >= d) & (df["startTime"] < d + pd.Timedelta(days=1))]
    for c in ["startTime", "publishTime", "cutoff"]:
        df[c] = df[c].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df.to_dict("records")


@app.get("/api/metrics")
def get_metrics(cutoff_hour: int = Query(CUTOFF_HOUR, ge=0, le=23)):
    return metrics(frame(cutoff_hour))


@app.get("/api/metrics/by-hour")
def by_hour(cutoff_hour: int = Query(CUTOFF_HOUR, ge=0, le=23)):
    df = frame(cutoff_hour)
    df = df.assign(hour=df["startTime"].dt.hour,
                   abs_err=df["error"].abs(), sq=df["error"] ** 2)
    g = df.groupby("hour").agg(mae=("abs_err", "mean"),
                               bias=("error", "mean"), mse=("sq", "mean"))
    g["rmse"] = g["mse"] ** 0.5
    return g.drop(columns="mse").reset_index().to_dict("records")


@app.get("/api/metrics/by-day")
def by_day(cutoff_hour: int = Query(CUTOFF_HOUR, ge=0, le=23)):
    df = frame(cutoff_hour)
    df = df.assign(day=df["startTime"].dt.strftime("%Y-%m-%d"),
                   abs_err=df["error"].abs())
    g = df.groupby("day").agg(mae=("abs_err", "mean"), bias=("error", "mean"))
    return g.reset_index().to_dict("records")