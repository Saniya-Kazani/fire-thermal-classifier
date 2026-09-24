// src/data/mockData.js
// Fake data for the demo. Later we replace this with a real fetch() call.
// Coordinates are approximate and locations are for demo only.

// The 5 categories: label + color used by the map markers, legend and chart
export const CATEGORIES = {
  industrial_flare: { label: 'Industrial Flare', color: '#f97316' },
  accident_explosion: { label: 'Accident / Explosion', color: '#dc2626' },
  crop_burning: { label: 'Crop Burning', color: '#eab308' },
  coal_seam_fire: { label: 'Coal-Seam Fire', color: '#7c3aed' },
  wildfire: { label: 'Wildfire', color: '#16a34a' },
}

// Makes 14 days of fake history ending on 23 Sep 2026.
// base = typical heat level, swing = how much it wobbles,
// spikeDay = which day (0-13) has a big jump (use -1 for no spike)
function makeHistory(base, swing, spikeDay) {
  const history = []
  const end = new Date('2026-09-23')
  for (let i = 0; i < 14; i++) {
    const day = new Date(end)
    day.setDate(end.getDate() - (13 - i))
    let frp = base + swing * Math.sin(i * 1.3)
    if (i === spikeDay) frp += base * 2
    history.push({
      date: day.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
      frp: Math.max(0, Math.round(frp)),
    })
  }
  return history
}

// frp = Fire Radiative Power in megawatts (how intense the heat is)
// brightness = brightness temperature in Kelvin
export const SITES = [
  {
    id: 's1',
    name: 'Refinery Flare Stack A',
    lat: 29.431,
    lng: 76.928,
    category: 'industrial_flare',
    confidence: 96,
    frp: 42,
    brightness: 341,
    detectedAt: '2026-09-23T09:40:00',
    satellite: 'VIIRS',
    history: makeHistory(40, 6, -1),
  },
  {
    id: 's2',
    name: 'Petrochemical Complex Flare',
    lat: 29.425,
    lng: 76.945,
    category: 'industrial_flare',
    confidence: 93,
    frp: 37,
    brightness: 338,
    detectedAt: '2026-09-23T09:40:00',
    satellite: 'VIIRS',
    history: makeHistory(35, 5, -1),
  },
  {
    id: 's3',
    name: 'Samalkha Industrial Estate',
    lat: 29.235,
    lng: 77.01,
    category: 'accident_explosion',
    confidence: 88,
    frp: 185,
    brightness: 367,
    detectedAt: '2026-09-23T13:15:00',
    satellite: 'VIIRS',
    history: makeHistory(5, 2, 13),
  },
  {
    id: 's4',
    name: 'Karnal Outskirts Farmland',
    lat: 29.686,
    lng: 76.99,
    category: 'crop_burning',
    confidence: 91,
    frp: 28,
    brightness: 334,
    detectedAt: '2026-09-23T11:05:00',
    satellite: 'MODIS',
    history: makeHistory(10, 8, 10),
  },
  {
    id: 's5',
    name: 'Assandh Paddy Fields',
    lat: 29.519,
    lng: 76.605,
    category: 'crop_burning',
    confidence: 84,
    frp: 22,
    brightness: 331,
    detectedAt: '2026-09-23T11:05:00',
    satellite: 'MODIS',
    history: makeHistory(8, 6, 11),
  },
  {
    id: 's6',
    name: 'Indri Farm Cluster',
    lat: 29.86,
    lng: 77.01,
    category: 'crop_burning',
    confidence: 79,
    frp: 19,
    brightness: 329,
    detectedAt: '2026-09-22T12:30:00',
    satellite: 'VIIRS',
    history: makeHistory(7, 5, 12),
  },
  {
    id: 's7',
    name: 'Kaithal Stubble Burning',
    lat: 29.801,
    lng: 76.399,
    category: 'crop_burning',
    confidence: 86,
    frp: 31,
    brightness: 336,
    detectedAt: '2026-09-22T12:30:00',
    satellite: 'VIIRS',
    history: makeHistory(12, 9, 9),
  },
  {
    id: 's8',
    name: 'Coal Stockyard (Smouldering)',
    lat: 29.6,
    lng: 76.45,
    category: 'coal_seam_fire',
    confidence: 82,
    frp: 15,
    brightness: 322,
    detectedAt: '2026-09-21T02:20:00',
    satellite: 'VIIRS',
    history: makeHistory(14, 2, -1),
  },
  {
    id: 's9',
    name: 'Yamunanagar Foothill Forest',
    lat: 30.13,
    lng: 77.28,
    category: 'wildfire',
    confidence: 90,
    frp: 64,
    brightness: 349,
    detectedAt: '2026-09-22T14:50:00',
    satellite: 'VIIRS',
    history: makeHistory(15, 10, 11),
  },
  {
    id: 's10',
    name: 'Kalesar Forest Belt',
    lat: 30.32,
    lng: 77.39,
    category: 'wildfire',
    confidence: 77,
    frp: 51,
    brightness: 344,
    detectedAt: '2026-09-22T14:50:00',
    satellite: 'MODIS',
    history: makeHistory(12, 8, 12),
  },
]

// Alerts feed: built from the sites, newest first
export const ALERTS = [...SITES]
  .sort((a, b) => new Date(b.detectedAt) - new Date(a.detectedAt))
  .map((site) => ({
    id: 'a-' + site.id,
    siteId: site.id,
    category: site.category,
    severity:
      site.category === 'accident_explosion' || site.frp >= 60 ? 'high' : 'medium',
    message: `${CATEGORIES[site.category].label} detected at ${site.name}`,
    time: site.detectedAt,
  }))