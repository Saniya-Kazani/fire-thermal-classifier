// src/components/AlertsFeed.jsx
// The live alerts list, newest first. Clicking an alert selects that site
// on the map. It receives the alerts, the selected site id, and a select
// function from App.jsx.

import { CATEGORIES } from '../data/mockData'

function AlertsFeed({ alerts, selectedSiteId, onSelectSite }) {
  return (
    <div className="rounded-lg bg-slate-700/50 p-3">
      {/* Title row with a pulsing "LIVE" dot */}
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-semibold">Live Alerts</h2>
        <span className="flex items-center gap-1 text-xs text-red-400">
          <span className="inline-block w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          LIVE
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-3">Click an alert to find it on the map.</p>

      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {alerts.map((alert) => {
          const category = CATEGORIES[alert.category]
          const isHigh = alert.severity === 'high'
          const isSelected = alert.siteId === selectedSiteId
          const timeText = new Date(alert.time).toLocaleString('en-IN', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          })

          return (
            <button
              key={alert.id}
              onClick={() => onSelectSite(alert.siteId)}
              className={`block w-full text-left rounded bg-slate-800 p-2 hover:bg-slate-600 border-l-4 ${
                isSelected ? 'ring-1 ring-white' : ''
              }`}
              style={{ borderLeftColor: category.color }}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                    isHigh ? 'bg-red-600' : 'bg-amber-600'
                  }`}
                >
                  {alert.severity}
                </span>
                <span className="text-[10px] text-slate-400">{timeText}</span>
              </div>
              <p className="text-xs">{alert.message}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default AlertsFeed