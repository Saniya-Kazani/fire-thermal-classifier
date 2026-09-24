// src/components/SummaryBar.jsx
// A row of key numbers at the top of the dashboard.
// It receives the sites and alerts currently visible (after the category
// filter) from App.jsx, so the numbers always match the map.
// The grid shows 2 boxes per row on phones and 4 in one row on bigger screens.

// One number box (label on top, big value below)
function StatBox({ label, value, valueClass = '' }) {
  return (
    <div className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`text-xl font-bold ${valueClass}`}>{value}</p>
    </div>
  )
}

function SummaryBar({ sites, alerts }) {
  const highCount = alerts.filter((alert) => alert.severity === 'high').length

  // Hottest site = the one with the biggest FRP (heat power)
  const hottest = sites.reduce(
    (best, site) => (!best || site.frp > best.frp ? site : best),
    null
  )

  // Latest detection time (ISO date strings sort correctly as plain text)
  const latest = sites.reduce(
    (max, site) => (site.detectedAt > max ? site.detectedAt : max),
    ''
  )
  const latestText = latest
    ? new Date(latest).toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '--'

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 px-4 py-3 bg-slate-900">
      <StatBox label="Detections" value={sites.length} />
      <StatBox
        label="High severity"
        value={highCount}
        valueClass={highCount > 0 ? 'text-red-400' : ''}
      />
      <StatBox label="Hottest (FRP)" value={hottest ? `${hottest.frp} MW` : '--'} />
      <StatBox label="Last detection" value={latestText} valueClass="text-base" />
    </div>
  )
}

export default SummaryBar