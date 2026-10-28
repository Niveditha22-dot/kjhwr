import { useEffect, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function get(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`Request failed (${r.status})`);
  return r.json();
}

const fmt = (n) => Math.round(n).toLocaleString("en-GB");

export default function App() {
  const [cutoff, setCutoff] = useState(9);
  const [day, setDay] = useState("2026-01-12");
  const [mode, setMode] = useState("day");
  const [metrics, setMetrics] = useState(null);
  const [series, setSeries] = useState([]);
  const [byHour, setByHour] = useState([]);
  const [byDay, setByDay] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const q = `cutoff_hour=${cutoff}`;
    const seriesPath = mode === "day"
      ? `/api/series?${q}&day=${day}`
      : `/api/series?${q}`;
    Promise.all([
      get(`/api/metrics?${q}`),
      get(seriesPath),
      get(`/api/metrics/by-hour?${q}`),
      get(`/api/metrics/by-day?${q}`),
    ])
      .then(([m, s, h, d]) => {
        if (cancelled) return;
        setMetrics(m);
        setSeries(s);
        setByHour(h);
        setByDay(d);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [cutoff, day, mode]);

  const chartData = series.map((r) => ({
    label: mode === "day"
      ? r.startTime.slice(11, 16)
      : `${r.startTime.slice(5, 10)} ${r.startTime.slice(11, 16)}`,
    Forecast: r.forecast,
    Actual: r.actual,
  }));

  return (
    <div className="page">
      <h1>GB wind: forecast vs actual</h1>
      <p className="sub">
        What a day-ahead buyer could see when deciding, and how accurate it was. January 2026 deliveries, national wind, Elexon data.
      </p>

      <div className="controls">
        <label>
          Decision time (UTC, day before delivery)
          <select value={cutoff} onChange={(e) => setCutoff(Number(e.target.value))}>
            {Array.from({ length: 24 }, (_, h) => (
              <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
            ))}
          </select>
        </label>
        <label>
          Delivery day
          <input type="date" value={day} min="2026-01-02" max="2026-02-01"
                 onChange={(e) => e.target.value && setDay(e.target.value)} />
        </label>
        <div>
          <button className={`toggle ${mode === "day" ? "active" : ""}`} onClick={() => setMode("day")}>One day</button>{" "}
          <button className={`toggle ${mode === "month" ? "active" : ""}`} onClick={() => setMode("month")}>Whole month</button>
        </div>
        <p className="note">
          For each hour, we show the latest forecast published before {String(cutoff).padStart(2, "0")}:00 on the day before delivery.
          Times are UTC, which equals UK time in January.
        </p>
      </div>

      {loading && <div className="status">Loading…</div>}
      {error && <div className="status error">Could not load data: {error}. Is the API running?</div>}

      {metrics && (
        <div className="cards">
          <div className="card"><div className="label">Mean absolute error</div>
            <div className="value">{fmt(metrics.mae)} MW</div>
            <div className="hint">Typical size of the miss</div></div>
          <div className="card"><div className="label">RMSE</div>
            <div className="value">{fmt(metrics.rmse)} MW</div>
            <div className="hint">Penalises large misses</div></div>
          <div className="card"><div className="label">Bias</div>
            <div className="value">{metrics.bias > 0 ? "+" : ""}{fmt(metrics.bias)} MW</div>
            <div className="hint">{metrics.bias > 0 ? "Forecast is above actual on average" : "Forecast is below actual on average"}</div></div>
          <div className="card"><div className="label">Hours compared</div>
            <div className="value">{metrics.n}</div>
            <div className="hint">All of January 2026 deliveries</div></div>
        </div>
      )}

      <div className="panel">
        <h2>Forecast vs actual wind generation</h2>
        <p>{mode === "day" ? `Delivery day ${day}` : "Every hour of January 2026"}</p>
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" minTickGap={mode === "day" ? 20 : 60} />
            <YAxis tickFormatter={fmt} unit=" MW" width={90} />
            <Tooltip formatter={(v) => `${fmt(v)} MW`} />
            <Legend />
            <Line type="monotone" dataKey="Forecast" stroke="#2563eb" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="Actual" stroke="#16a34a" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h2>Average error by hour of day</h2>
        <p>Bias above zero means the forecast was too high.</p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={byHour}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis tickFormatter={fmt} width={70} />
            <Tooltip formatter={(v) => `${fmt(v)} MW`} />
            <Legend />
            <ReferenceLine y={0} stroke="#1a2433" />
            <Bar dataKey="mae" name="MAE" fill="#f59e0b" />
            <Bar dataKey="bias" name="Bias" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h2>Bias by delivery day</h2>
        <p>Whether the over-forecasting is steady or driven by a few days.</p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={byDay}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" tickFormatter={(d) => d.slice(5)} minTickGap={16} />
            <YAxis tickFormatter={fmt} width={70} />
            <Tooltip formatter={(v) => `${fmt(v)} MW`} />
            <ReferenceLine y={0} stroke="#1a2433" />
            <Bar dataKey="bias" name="Bias" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}