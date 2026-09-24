// src/components/MapView.jsx
// The interactive map with pulsing fire markers and a live
// latitude/longitude readout that follows the mouse (like NASA FIRMS).

import { MapContainer, TileLayer, Marker, Tooltip, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { useEffect, useState } from 'react'
import { CATEGORIES } from '../data/mockData'

// Demo region (Panipat area): [[south, west], [north, east]]
const REGION_BOUNDS = [
  [29.0, 76.0],
  [30.5, 77.5],
]

// A site is "urgent" (faster pulse) if it is an explosion or very hot.
// Same rule the alerts use for the HIGH badge.
function isUrgent(site) {
  return site.category === 'accident_explosion' || site.frp >= 60
}

// Builds the marker icon. We remember icons already made (the "cache"),
// so the same icon object is reused. Otherwise Leaflet would redraw every
// marker on each update and the pulse animation would restart.
const iconCache = {}
function getIcon(color, urgent, selected) {
  const key = `${color}-${urgent}-${selected}`
  if (!iconCache[key]) {
    const size = selected ? 26 : 18
    iconCache[key] = L.divIcon({
      className: 'fire-marker',
      html: `<div class="fire-dot ${urgent ? 'fast' : ''} ${selected ? 'selected' : ''}" style="--c:${color}"></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    })
  }
  return iconCache[key]
}

// Moves the map to the selected site. Draws nothing.
function FlyToSelected({ site }) {
  const map = useMap()

  useEffect(() => {
    if (site) {
      map.flyTo([site.lat, site.lng], Math.max(map.getZoom(), 10), { duration: 0.8 })
    }
  }, [site, map])

  return null
}

// The small bar at the bottom showing the mouse position in degrees.
// It keeps its own memory, so the markers are not redrawn when the mouse moves.
function CursorReadout() {
  const [pos, setPos] = useState(null)

  useMapEvents({
    mousemove: (e) =>
      setPos({ lat: e.latlng.lat, lng: e.latlng.lng, zoom: e.target.getZoom() }),
    mouseout: () => setPos(null),
  })

  const latText = pos ? `${Math.abs(pos.lat).toFixed(4)}° ${pos.lat >= 0 ? 'N' : 'S'}` : '--'
  const lngText = pos ? `${Math.abs(pos.lng).toFixed(4)}° ${pos.lng >= 0 ? 'E' : 'W'}` : '--'

  return (
    <div
      className="absolute bottom-2 left-2 z-[1000] pointer-events-none rounded bg-slate-900/85 px-3 py-1 text-xs font-mono text-slate-200 border border-slate-600"
    >
      Lat {latText} &nbsp;|&nbsp; Lng {lngText}
      {pos && <span className="text-slate-400"> &nbsp;|&nbsp; Zoom {pos.zoom}</span>}
    </div>
  )
}

function MapView({ sites, selectedSiteId, onSelectSite }) {
  const selectedSite = sites.find((site) => site.id === selectedSiteId)

  return (
    <MapContainer
      bounds={REGION_BOUNDS}
      className="h-full w-full rounded-lg"
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FlyToSelected site={selectedSite} />
      <CursorReadout />

      {sites.map((site) => {
        const color = CATEGORIES[site.category].color
        const isSelected = site.id === selectedSiteId

        return (
          <Marker
            key={site.id}
            position={[site.lat, site.lng]}
            icon={getIcon(color, isUrgent(site), isSelected)}
            zIndexOffset={isSelected ? 1000 : 0}
            eventHandlers={{ click: () => onSelectSite(site.id) }}
          >
            <Tooltip direction="top" offset={[0, -12]}>
              {site.name}
            </Tooltip>
          </Marker>
        )
      })}
    </MapContainer>
  )
}

export default MapView