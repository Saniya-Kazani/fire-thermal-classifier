// src/components/SiteDetailPanel.jsx
// Shows details of the selected site plus a 14-day history chart.
// It receives the selected site (or undefined if none) and a close function from App.jsx.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { CATEGORIES } from '../data/mockData'

// A small reusable box for one number (label on top, value below)
function Stat({ label, value }) {
  return (
    <div className="rounded bg-slate-800 p-2">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  )
}

function SiteDetailPanel({ site, onClose }) {
  // Nothing selected yet: show a hint instead
  if (!site) {
    return (
      <div className="rounded-lg bg-slate-700/50 p-3">
        <h2 className="text-sm font-semibold mb-1">Site Details</h2>
        <p className="text-xs text-slate-400">
          Click a marker on the map to see its details and history.
        </p>
      </div>
    )
  }

  const category = CATEGORIES[site.category]
  const detectedText = new Date(site.detectedAt).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className="rounded-lg bg-slate-700/50 p-3">
      {/* Title row with close button */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h2 className="text-sm font-semibold">{site.name}</h2>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white text-lg leading-none"
          aria-label="Close details"
        >
          &times;
        </button>
      </div>

      {/* Category badge */}
      <span
        className="inline-block text-xs font-medium px-2 py-0.5 rounded-full mb-3"
        style={{ backgroundColor: category.color }}
      >
        {category.label}
      </span>

      {/* Key numbers */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <Stat label="Confidence" value={`${site.confidence}%`} />
        <Stat label="Heat power (FRP)" value={`${site.frp} MW`} />
        <Stat label="Brightness" value={`${site.brightness} K`} />
        <Stat label="Satellite" value={site.satellite} />
      </div>
      <p className="text-xs text-slate-400 mb-3">Detected: {detectedText}</p>

      {/* History chart */}
      <p className="text-xs font-semibold mb-1">Heat power, last 14 days (MW)</p>
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={site.history} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#475569" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 10 }} interval={3} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey="frp"
              name="FRP (MW)"
              stroke={category.color}
              strokeWidth={2}
              dot={{ r: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default SiteDetailPanel