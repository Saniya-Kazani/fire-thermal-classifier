// src/components/IndustrialAIDashboard.jsx
// Industrial Fire AI Triage & Anomaly Detection Dashboard Component
// Uses Isolation Forest Anomaly Scores + BallTree OSM Spatial Matching

import { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { fetchIndustrialAISummary, fetchIndustrialAIAlerts, getIndustrialAICsvUrl } from '../data/api'

// Default India bounds
const INDIA_BOUNDS = [
  [8.0, 68.0],
  [36.0, 96.0],
]

const PRIORITY_COLORS = {
  HIGH: '#ef4444',
  MEDIUM: '#f97316',
  LOW: '#3b82f6',
}

function MapFlyTo({ alert }) {
  const map = useMap()
  useEffect(() => {
    if (alert && alert.latitude && alert.longitude) {
      map.flyTo([Number(alert.latitude), Number(alert.longitude)], Math.max(map.getZoom(), 8), { duration: 0.8 })
    }
  }, [alert, map])
  return null
}

export default function IndustrialAIDashboard() {
  const [summary, setSummary] = useState({ total_records: 0, total_anomalies: 0, priority_counts: { HIGH: 0, MEDIUM: 0, LOW: 0 } })
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [selectedPriorities, setSelectedPriorities] = useState({ HIGH: true, MEDIUM: true, LOW: true })
  const [search, setSearch] = useState('')
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [isRunningPipeline, setIsRunningPipeline] = useState(false)

  // Load summary and alerts
  const loadData = async (signal) => {
    setLoading(true)
    try {
      const activePriorities = Object.keys(selectedPriorities).filter((k) => selectedPriorities[k]).join(',')
      const [sumRes, alertsRes] = await Promise.all([
        fetchIndustrialAISummary(signal),
        fetchIndustrialAIAlerts({ priority: activePriorities, search, limit: 1000 }, signal),
      ])
      setSummary(sumRes)
      setAlerts(alertsRes.alerts || [])
      setError(null)
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to connect to Industrial Fire AI backend')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    loadData(controller.signal)
    return () => controller.abort()
  }, [selectedPriorities, search])

  const togglePriority = (prio) => {
    setSelectedPriorities((prev) => ({ ...prev, [prio]: !prev[prio] }))
  }

  const handleRunPipeline = async () => {
    setIsRunningPipeline(true)
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/industrial-ai/run-pipeline`, { method: 'POST' })
      const data = await res.json()
      if (data.status === 'success') {
        await loadData()
      }
    } catch (err) {
      alert('Pipeline execution failed: ' + err.message)
    } finally {
      setIsRunningPipeline(false)
    }
  }

  const activePriorityString = useMemo(() => {
    return Object.keys(selectedPriorities).filter((k) => selectedPriorities[k]).join(',')
  }, [selectedPriorities])

  const csvDownloadUrl = getIndustrialAICsvUrl({ priority: activePriorityString, search })

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white overflow-y-auto lg:overflow-hidden p-4 space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-800 p-4 rounded-xl border border-slate-700">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xl">🔥</span>
            <h2 className="text-lg font-bold text-amber-400">Industrial Fire AI Triage & Anomaly Module</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Isolation Forest Anomaly Scoring &bull; BallTree OSM Industrial Distance Matcher &bull; Multi-Factor Risk Priority
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            placeholder="Search industry name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-amber-500 w-48 sm:w-64"
          />

          <a
            href={csvDownloadUrl}
            download="filtered_industrial_alerts.csv"
            className="px-3 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center space-x-1 transition-colors"
          >
            <span>📥 Export CSV</span>
          </a>

          <button
            onClick={handleRunPipeline}
            disabled={isRunningPipeline}
            className="px-3 py-1.5 text-xs font-semibold bg-amber-600 hover:bg-amber-500 disabled:bg-slate-700 text-white rounded-lg transition-colors"
          >
            {isRunningPipeline ? 'Running AI...' : '⚡ Re-run AI Pipeline'}
          </button>
        </div>
      </div>

      {/* Metrics Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-800 p-3 rounded-xl border border-slate-700 text-center">
          <div className="text-2xl font-bold text-slate-100">{summary.total_records || alerts.length}</div>
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Anomalies</div>
        </div>

        <button
          onClick={() => togglePriority('HIGH')}
          className={`p-3 rounded-xl border text-center transition-all ${
            selectedPriorities.HIGH ? 'bg-red-950/60 border-red-500 text-red-200' : 'bg-slate-800/60 border-slate-700 text-slate-500 opacity-60'
          }`}
        >
          <div className="text-2xl font-bold text-red-400">{summary.priority_counts?.HIGH || 0}</div>
          <div className="text-xs uppercase tracking-wider font-semibold flex items-center justify-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
            <span>HIGH Priority</span>
          </div>
        </button>

        <button
          onClick={() => togglePriority('MEDIUM')}
          className={`p-3 rounded-xl border text-center transition-all ${
            selectedPriorities.MEDIUM ? 'bg-orange-950/60 border-orange-500 text-orange-200' : 'bg-slate-800/60 border-slate-700 text-slate-500 opacity-60'
          }`}
        >
          <div className="text-2xl font-bold text-orange-400">{summary.priority_counts?.MEDIUM || 0}</div>
          <div className="text-xs uppercase tracking-wider font-semibold flex items-center justify-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-orange-500 inline-block"></span>
            <span>MEDIUM Priority</span>
          </div>
        </button>

        <button
          onClick={() => togglePriority('LOW')}
          className={`p-3 rounded-xl border text-center transition-all ${
            selectedPriorities.LOW ? 'bg-blue-950/60 border-blue-500 text-blue-200' : 'bg-slate-800/60 border-slate-700 text-slate-500 opacity-60'
          }`}
        >
          <div className="text-2xl font-bold text-blue-400">{summary.priority_counts?.LOW || 0}</div>
          <div className="text-xs uppercase tracking-wider font-semibold flex items-center justify-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block"></span>
            <span>LOW Priority</span>
          </div>
        </button>
      </div>

      {/* Content Area: Map + Alert Table Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-[500px]">
        {/* Interactive Map */}
        <div className="lg:col-span-7 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden relative min-h-[400px]">
          <MapContainer bounds={INDIA_BOUNDS} className="h-full w-full" scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapFlyTo alert={selectedAlert} />

            {alerts.map((alert, idx) => {
              const prio = alert.investigation_priority || 'LOW'
              const color = PRIORITY_COLORS[prio] || '#94a3b8'
              const lat = Number(alert.latitude)
              const lng = Number(alert.longitude)

              if (isNaN(lat) || isNaN(lng)) return null

              return (
                <CircleMarker
                  key={idx}
                  center={[lat, lng]}
                  radius={prio === 'HIGH' ? 8 : prio === 'MEDIUM' ? 6 : 4}
                  pathOptions={{ color, fillColor: color, fillOpacity: 0.8 }}
                  eventHandlers={{ click: () => setSelectedAlert(alert) }}
                >
                  <Popup maxW={320}>
                    <div className="text-slate-900 text-xs space-y-1">
                      <div className="font-bold border-b pb-1 flex justify-between items-center">
                        <span style={{ color }}>{prio} Priority Alert</span>
                        <span className="text-[10px] text-slate-500">{alert.acq_date}</span>
                      </div>
                      <div><b>Satellite:</b> {alert.satellite}</div>
                      <div><b>FRP:</b> {alert.frp} MW</div>
                      <div><b>Brightness:</b> {alert.brightness} K</div>
                      <div><b>Nearest Industry:</b> {alert.nearest_industry_name}</div>
                      <div><b>Distance:</b> {Number(alert.nearest_industry_distance_km).toFixed(2)} km</div>
                      <div><b>AI Score:</b> {Number(alert.anomaly_score || 0).toFixed(4)}</div>
                      <div className="italic text-slate-600 pt-1 border-t mt-1">{alert.classification_reason}</div>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
          </MapContainer>
        </div>

        {/* Alerts Table */}
        <div className="lg:col-span-5 bg-slate-800 border border-slate-700 rounded-xl flex flex-col min-h-[400px]">
          <div className="p-3 border-b border-slate-700 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-200">
              🚨 AI Alert Records ({alerts.length})
            </h3>
            {loading && <span className="text-xs text-amber-400 animate-pulse">Loading dataset...</span>}
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-2 max-h-[500px]">
            {alerts.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                {loading ? 'Fetching records...' : 'No alerts match current priority filter or search.'}
              </div>
            ) : (
              alerts.slice(0, 100).map((alert, idx) => {
                const prio = alert.investigation_priority || 'LOW'
                const badgeColor = prio === 'HIGH' ? 'bg-red-950 text-red-300 border-red-700' : prio === 'MEDIUM' ? 'bg-orange-950 text-orange-300 border-orange-700' : 'bg-blue-950 text-blue-300 border-blue-700'

                const isSelected = selectedAlert === alert

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedAlert(alert)}
                    className={`p-3 rounded-lg border transition-all cursor-pointer text-xs space-y-1.5 ${
                      isSelected ? 'bg-slate-700/90 border-amber-500' : 'bg-slate-900/60 border-slate-700 hover:border-slate-500'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${badgeColor}`}>
                        {prio} PRIORITY
                      </span>
                      <span className="text-slate-400 text-[11px]">{alert.acq_date} &bull; {alert.satellite}</span>
                    </div>

                    <div className="font-semibold text-slate-200">
                      {alert.nearest_industry_name || 'Unknown Industry'}
                      <span className="text-slate-400 font-normal ml-1">
                        ({Number(alert.nearest_industry_distance_km).toFixed(2)} km)
                      </span>
                    </div>

                    <div className="flex justify-between text-slate-300 text-[11px]">
                      <span>FRP: <b>{alert.frp} MW</b></span>
                      <span>Brightness: <b>{alert.brightness} K</b></span>
                      <span>Score: <b>{Number(alert.anomaly_score || 0).toFixed(3)}</b></span>
                    </div>

                    <p className="text-slate-400 text-[11px] italic">
                      {alert.classification_reason}
                    </p>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
