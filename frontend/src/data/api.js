import { CATEGORIES } from './mockData'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'https://fire-thermal-classifier.onrender.com'
).replace(/\/$/, '')

const CATEGORY_MAP = {
  gas_flare: 'industrial_flare',
  desert_glare_false_alarm: 'false_alarm',
  unclassified: 'unclassified',
}

export function normalizeCategory(category) {
  return CATEGORY_MAP[category] || category || 'unclassified'
}

function formatDateTime(date, time) {
  if (!date) return ''
  const normalizedTime = String(time || '0000').padStart(4, '0')
  return `${date}T${normalizedTime.slice(0, 2)}:${normalizedTime.slice(2)}:00Z`
}

export function normalizeHotspot(hotspot) {
  const category = normalizeCategory(hotspot.category)
  const date = formatDateTime(hotspot.acq_date, hotspot.acq_time)
  const location = `${Number(hotspot.latitude).toFixed(3)}, ${Number(hotspot.longitude).toFixed(3)}`

  return {
    id: String(hotspot.id),
    name: `${CATEGORIES[category]?.label || 'Thermal'} detection (${location})`,
    lat: Number(hotspot.latitude),
    lng: Number(hotspot.longitude),
    category,
    confidence: Math.round(Number(hotspot.classification_confidence || 0) * 100),
    frp: Number(hotspot.frp || 0),
    brightness: Number(hotspot.brightness || 0),
    detectedAt: date,
    satellite: hotspot.satellite || hotspot.sensor || 'Unknown',
    history: [],
    classificationReason: hotspot.classification_reason,
  }
}

export function normalizeAlert(alert, hotspots) {
  const site = hotspots.find((hotspot) => hotspot.id === String(alert.hotspot_id))
  const category = normalizeCategory(alert.category)
  return {
    id: String(alert.id),
    siteId: String(alert.hotspot_id),
    category,
    severity: alert.severity,
    message: `${CATEGORIES[category]?.label || 'Thermal event'} detected${site ? ` at ${site.name}` : ''}${alert.reason ? `: ${alert.reason}` : ''}`,
    time: alert.created_at,
  }
}

async function getJson(path, signal) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal })
  if (!response.ok) throw new Error(`API ${path} returned ${response.status}`)
  return response.json()
}

export async function fetchDashboardData(signal) {
  const [hotspotRows, alertRows] = await Promise.all([
    getJson('/api/hotspots?limit=1000', signal),
    getJson('/api/alerts?limit=200', signal),
  ])
  if (!Array.isArray(hotspotRows) || !Array.isArray(alertRows)) {
    throw new Error('Unexpected API response; expected arrays from hotspots and alerts')
  }
  const sites = hotspotRows.map(normalizeHotspot)
  return { sites, alerts: alertRows.map((alert) => normalizeAlert(alert, sites)) }
}

export async function fetchHotspotHistory(hotspotId, signal) {
  const rows = await getJson(`/api/hotspots/${encodeURIComponent(hotspotId)}/history`, signal)
  if (!Array.isArray(rows)) throw new Error('Unexpected hotspot history response')
  return rows.map((point) => ({
    date: point.acq_date,
    frp: Number(point.frp || 0),
    brightness: Number(point.brightness || 0),
  }))
}