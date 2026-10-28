import pandas as pd
from analysis import load, compare, metrics

ac, fc = load()

# 1. Does shifting actuals by +/- 30 or 60 min change the picture?
for shift in [-60, -30, 0, 30, 60]:
    a = ac.copy()
    a["startTime"] = a["startTime"] + pd.Timedelta(minutes=shift)
    print(shift, metrics(compare(a, fc)))

# 2. Average forecast vs actual
df = compare(ac, fc)
print(df[["forecast", "actual"]].mean())

# 3. Daily bias, to see if it's steady or driven by a few days
print(df.groupby(df["startTime"].dt.date)["error"].mean().round(0))