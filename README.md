# 🌬️ GB wind forecast vs actual

![Python](https://img.shields.io/badge/backend-FastAPI-009688) ![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb) ![Docker](https://img.shields.io/badge/run%20with-Docker-2496ed) ![Tests](https://img.shields.io/badge/tests-pytest-green)

A web app for a **day-ahead power buyer in Great Britain**. It answers two questions:

1. What wind forecast was actually available when the buying decision had to be made?
2. How accurate were those forecasts?

| Link | URL |
|---|---|
| 🌐 Live app | https://kjhwr-7yfm.vercel.app/ |
| ⚙️ API | https://kjhwr-tau.vercel.app/ (docs at [`/docs`](https://kjhwr-tau.vercel.app/docs)) |
| 🎥 Video demo | ADD_YOUTUBE_LINK_HERE |

Scope: national wind only, from Elexon (FUELHH actuals, WINDFOR forecasts), for purchase decisions made in January 2026.

## Contents

- [Quick try (no install)](#quick-try-no-install)
- [Run it on your computer](#run-it-on-your-computer)
- [How it works](#how-it-works)
- [Headline result](#headline-result)
- [Assumptions and limits](#assumptions-and-limits)
- [Repository layout](#repository-layout)
- [Deployment](#deployment)
- [Use of AI tools](#use-of-ai-tools)

## Quick try (no install)

1. Open the [live app](https://kjhwr-7yfm.vercel.app/). The first load can take a few seconds.
2. Change the **decision time** and watch the metrics update.
3. Pick a **delivery day**, or switch to **Whole month**.
4. Try the API directly: [`/api/metrics?cutoff_hour=9`](https://kjhwr-tau.vercel.app/api/metrics?cutoff_hour=9)

## Run it on your computer

### Step 1: Get the code

Pick one:

- **With git:**
  ```
  git clone https://github.com/Niveditha22-dot/kjhwr.git
  cd kjhwr
  ```
- **Without git:** On the repo page, click the green **Code** button, choose **Download ZIP**, unzip it, and open a terminal inside the unzipped `kjhwr` folder.

### Step 2: Choose how to run it

#### Option A: Docker (recommended)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it. Wait until it says the engine is running.
2. In the `kjhwr` folder, run:
   ```
   docker compose up --build
   ```
3. Wait for the build to finish (a few minutes the first time).
4. Open http://localhost:5173 in your browser. The API is at http://localhost:8000/docs.
5. To stop, press `Ctrl+C`, then run `docker compose down`.

#### Option B: Without Docker

<details>
<summary>Click to expand</summary>

You need Python 3.12 or newer and Node.js 20 or newer.

**Terminal 1: backend**

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

On Mac or Linux, use `source venv/bin/activate` instead of `venv\Scripts\activate`.

Check http://127.0.0.1:8000/docs loads.

**Terminal 2: frontend** (leave Terminal 1 running)

```
cd frontend
npm install
npm run dev
```

Open the address it prints (usually http://localhost:5173).

</details>

### Step 3: Run the tests (optional)

```
cd backend
venv\Scripts\activate
pytest -v
```

You should see `2 passed`.

## How it works

1. **Decision time.** The buyer decides on day D-1 and delivers on day D. For each target hour, the app takes the most recent WINDFOR forecast published at or before the decision time on the previous day (default 09:00 UTC, adjustable in the UI). Later forecasts are excluded because the buyer could not have seen them. Some forecasts are published after the hour they predict, so this filter matters.
2. **Why 09:00.** EPEX SPOT lists the GB day-ahead auction closing at 10:20 CET (09:20 UK time), and an older Nord Pool specification gave 09:50. 09:00 sits before both and leaves time to bid. WINDFOR publishes at :30 past the hour, so any cutoff from 09:00 to 09:29 selects the same forecast.
3. **Accuracy.** The chosen forecast is joined to the FUELHH actual with the same `startTime`. Error is forecast minus actual, so positive means the forecast was too high. Metrics are MAE, RMSE and bias, also broken down by hour of day and by delivery day.
4. **Time zone.** All times are UTC, which equals UK time in January.

## Headline result

09:00 decision time, 744 hourly points:

| Metric | Value |
|---|---|
| MAE | 2,022 MW |
| RMSE | 2,497 MW |
| Bias | +1,746 MW |

- The forecast available at decision time was higher than actual wind on average. A buyer relying on it alone would tend to under-buy from other sources.
- The bias was positive on most delivery days, so it was persistent. I did not investigate the cause. It could be forecast error or a difference in how the two datasets define wind generation.
- `backend/check.py` shifts the actuals by up to 60 minutes. Accuracy barely changes, which suggests the timestamps are aligned correctly.

## Assumptions and limits

- WINDFOR forecasts are hourly and FUELHH actuals are half-hourly, so only the hourly points are compared.
- The decision time is one fixed time on D-1. Real desks may decide at different times, which is why it is adjustable.
- The data was downloaded once with `backend/fetch_data.py` and stored as CSV in `backend/data/`. The app is fast and does not depend on Elexon being up, but it is not live.
- One month of data, so results should not be generalised to other seasons.

## Repository layout

```
backend/
  main.py            FastAPI app and endpoints
  analysis.py        forecast selection and error metrics
  test_analysis.py   pytest tests for the cutoff logic and metrics
  fetch_data.py      downloads January data from Elexon into data/
  check.py           timestamp alignment sanity check
  data/              actuals.csv, forecasts.csv
  Dockerfile, requirements.txt
frontend/
  src/App.jsx        React dashboard (Recharts)
  Dockerfile         builds the app and serves it with nginx
docker-compose.yml   runs both services
```

## Deployment

Two Vercel projects from this repo: `backend` (FastAPI) and `frontend` (Vite). The frontend reads the API address from the `VITE_API_URL` environment variable at build time.

## Use of AI tools

I used Claude (Anthropic) as a coding assistant to plan the approach, draft code, and help debug setup and deployment problems. I ran and checked the results myself, and I can explain the code.
