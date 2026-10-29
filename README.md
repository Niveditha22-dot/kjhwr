# GB wind forecast vs actual

A web app for a day-ahead power buyer in Great Britain. It shows the latest wind forecast that was available when the buying decision had to be made, and measures how accurate those forecasts were.

- **Live app:** https://kjhwr-7yfm.vercel.app/
- **API:** https://kjhwr-tau.vercel.app/ (try `/api/metrics?cutoff_hour=9`, interactive docs at `/docs`)
- **Video demo:** ADD_YOUTUBE_LINK_HERE

Scope is national wind generation from Elexon only (FUELHH for actuals, WINDFOR for forecasts), for deliveries whose purchase decisions fall in January 2026.

## Approach

1. **Decision time.** The buyer decides on day D-1 and delivers on day D. For each target hour, I take the most recent WINDFOR forecast with `publishTime` at or before a decision time on the previous day (default 09:00 UTC, adjustable in the UI). This stops later forecasts, which a buyer could not have had, from leaking in. Some forecasts are published after the hour they predict, so this matters.
2. **Why 09:00.** EPEX SPOT lists the GB day-ahead auction closing at 10:20 CET (09:20 UK time), and an older Nord Pool specification gave 09:50. 09:00 sits before both and leaves time to bid. WINDFOR publishes at :30 past the hour, so any cutoff from 09:00 to 09:29 selects the same forecast.
3. **Accuracy.** The selected forecast is joined to the FUELHH actual with the same `startTime`. Error is forecast minus actual, so positive means the forecast was too high. Metrics are MAE, RMSE and bias, also broken down by hour of day and by delivery day.
4. **Time.** All times are UTC, which equals UK time in January.

## Headline result (09:00 decision time, 744 hourly points)

- MAE 2,022 MW, RMSE 2,497 MW, bias +1,746 MW.
- The forecast available at decision time was higher than actual wind on average, so a buyer relying on it alone would tend to under-buy from other sources.
- The pattern is persistent, with positive daily bias on most days. I did not investigate the cause. It could be forecast error or a difference in how the two datasets define wind generation.

## Assumptions and limits

- WINDFOR forecasts are hourly and FUELHH actuals are half-hourly, so only the hourly points are compared.
- The decision time is a single fixed time on D-1. Real desks may decide at different times, which is why it is adjustable.
- The data was downloaded once with `backend/fetch_data.py` and stored as CSV in `backend/data/`, so the app is fast and does not depend on Elexon being up. It is not live.
- Single-month sample. Results should not be generalised to other seasons.

## Repository layout

```
backend/
  main.py            FastAPI app and endpoints
  analysis.py        forecast selection and error metrics
  test_analysis.py   pytest tests for the cutoff logic and metrics
  fetch_data.py      downloads January data from Elexon into data/
  check.py           sanity check: shifts actuals by +/-60 min to rule out timestamp misalignment
  data/              actuals.csv, forecasts.csv
  Dockerfile, requirements.txt
frontend/
  src/App.jsx        React dashboard (Recharts)
  Dockerfile         builds the app, serves it with nginx
docker-compose.yml   runs both services
```

## Run it

With Docker:

```
docker compose up --build
```

Open http://localhost:5173. The API is on http://localhost:8000.

Without Docker:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

In a second terminal:

```
cd frontend
npm install
npm run dev
```

Run the tests with `pytest -v` in `backend`.

## Deployment

Two Vercel projects from this repo: `backend` (FastAPI) and `frontend` (Vite). The frontend reads the API address from the `VITE_API_URL` environment variable.

## Use of AI tools

I used Claude (Anthropic) as a coding assistant to plan the approach, draft code, and help debug setup and deployment problems. I ran and checked the results myself, and I can explain the code.