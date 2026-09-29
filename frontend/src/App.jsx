// src/App.jsx
// The main page. It holds the "shared memory" (which site is selected,
// which categories are switched on) and lays out the screen.
// Layout: on a phone everything stacks in one scrolling column
// (header, summary, map, then the panels). On a large screen (lg:)
// the map sits on the left and the panels on the right.
// On a phone, selecting a site scrolls down to its details, and
// closing the details scrolls back up to the map.

import { useState, useEffect, useRef } from 'react'
import { CATEGORIES, SITES, ALERTS } from './data/mockData'
import { fetchDashboardData, fetchHotspotHistory } from './data/api'
import MapView from './components/MapView'
import CategoryLegend from './components/CategoryLegend'
import SiteDetailPanel from './components/SiteDetailPanel'
import AlertsFeed from './components/AlertsFeed'
import SummaryBar from './components/SummaryBar'
import IndustrialAIDashboard from './components/IndustrialAIDashboard'

// Same width where Tailwind's "lg:" layout switches on.
// Below this, the page is a single stacked column (phone layout).
function isPhoneLayout() {
  return window.innerWidth < 1024
}

function App() {
  const [activeTab, setActiveTab] = useState('classifier') // 'classifier' | 'industrial-ai'
  const [sites, setSites] = useState(SITES)
  const [alerts, setAlerts] = useState(ALERTS)
  const [dataSource, setDataSource] = useState('loading')
  const [apiError, setApiError] = useState('')
  // Shared memory: which site is selected (null = none)
  const [selectedSiteId, setSelectedSiteId] = useState(null)

  // Shared memory: which categories are switched on (all start as true)
  const [activeCategories, setActiveCategories] = useState(
    Object.fromEntries(Object.keys(CATEGORIES).map((key) => [key, true]))
  )

  // "Refs" are handles to real page elements, so we can scroll to them
  const mapSectionRef = useRef(null)
  const detailRef = useRef(null)

  useEffect(() => {
    let active = true
    let controller
    async function refresh() {
      controller = new AbortController()
      try {
        const data = await fetchDashboardData(controller.signal)
        if (!active) return
        setSites(data.sites)
        setAlerts(data.alerts)
        setDataSource('api')
        setApiError('')
      } catch (error) {
        if (!active || error.name === 'AbortError') return
        setDataSource((current) => current === 'api' ? 'api-error' : 'demo')
        setApiError(error.message)
      }
    }
    refresh()
    const intervalId = window.setInterval(refresh, 60_000)
    return () => {
      active = false
      controller?.abort()
      window.clearInterval(intervalId)
    }
  }, [])

  useEffect(() => {
    if (!selectedSiteId || dataSource !== 'api') return undefined
    const controller = new AbortController()
    fetchHotspotHistory(selectedSiteId, controller.signal)
      .then((history) => setSites((current) => current.map((site) =>
        site.id === selectedSiteId ? { ...site, history } : site
      )))
      .catch((error) => {
        if (error.name !== 'AbortError') setApiError(error.message)
      })
    return () => controller.abort()
  }, [selectedSiteId, dataSource])

  // Only the sites and alerts whose category is switched on
  const visibleSites = sites.filter((site) => activeCategories[site.category])
  const visibleAlerts = alerts.filter((alert) => activeCategories[alert.category])
  const selectedSite = sites.find((site) => site.id === selectedSiteId)

  // Flip one category on/off
  function toggleCategory(key) {
    setActiveCategories({ ...activeCategories, [key]: !activeCategories[key] })
  }

  // Whenever a site gets selected (from a dot or an alert), scroll the
  // detail panel into view. Only on phones: on a large screen the panel
  // is already visible beside the map.
  useEffect(() => {
    if (selectedSiteId && isPhoneLayout()) {
      detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [selectedSiteId])

  // The x button: clear the selection, and on phones scroll back up to the map
  function closeDetails() {
    setSelectedSiteId(null)
    if (isPhoneLayout()) {
      mapSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div className="min-h-screen lg:h-screen flex flex-col bg-slate-900 text-white">
      {/* Top bar with Navigation Tabs */}
      <header className="px-4 py-3 bg-slate-800 border-b border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-base sm:text-lg font-bold">
            Industrial Fire & Thermal Source Classification System
          </h1>
          <p className="text-xs text-slate-400">SIH 2026 - Integrated Multi-Model Thermal Intelligence</p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-700 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('classifier')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'classifier'
                ? 'bg-amber-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            🔥 Classifier View
          </button>
          <button
            onClick={() => setActiveTab('industrial-ai')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center space-x-1 ${
              activeTab === 'industrial-ai'
                ? 'bg-amber-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <span>🤖 Industrial AI Dashboard</span>
            <span className="bg-red-500 text-white text-[9px] px-1.5 py-0.2 rounded-full uppercase font-bold">New</span>
          </button>
        </div>
      </header>

      {dataSource !== 'api' && activeTab === 'classifier' && (
        <div className={`px-4 py-2 text-xs ${dataSource === 'api-error' ? 'bg-red-950 text-red-200' : 'bg-amber-950 text-amber-200'}`} role="status">
          {dataSource === 'loading'
            ? 'Connecting to backend...'
            : dataSource === 'api-error'
              ? `Backend refresh failed; showing last data. ${apiError}`
              : `Backend unavailable; showing demo data. ${apiError}`}
        </div>
      )}

      {activeTab === 'industrial-ai' ? (
        <div className="flex-1 min-h-0">
          <IndustrialAIDashboard />
        </div>
      ) : (
        <>
          {/* Key numbers (they follow the category filter) */}
          <SummaryBar sites={visibleSites} alerts={visibleAlerts} />

          <main className="flex flex-col lg:flex-row flex-1 lg:min-h-0">
            {/* Map: fixed height on phones, fills the left side on large screens */}
            <section
              ref={mapSectionRef}
              className="relative h-[55vh] lg:h-auto lg:flex-1"
            >
              <div className="absolute inset-2 lg:inset-4">
                <MapView
                  sites={visibleSites}
                  selectedSiteId={selectedSiteId}
                  onSelectSite={setSelectedSiteId}
                />
              </div>
            </section>

            {/* Panels: below the map on phones, a side column on large screens */}
            <aside className="w-full lg:w-80 bg-slate-800 border-t lg:border-t-0 lg:border-l border-slate-700 p-4 lg:overflow-y-auto space-y-4">
              <CategoryLegend
                activeCategories={activeCategories}
                onToggle={toggleCategory}
                sites={sites}
              />

              {/* This wrapper is the scroll target for the detail panel */}
              <div ref={detailRef}>
                <SiteDetailPanel site={selectedSite} onClose={closeDetails} />
              </div>

              <AlertsFeed
                alerts={visibleAlerts}
                selectedSiteId={selectedSiteId}
                onSelectSite={setSelectedSiteId}
              />
            </aside>
          </main>
        </>
      )}
    </div>
  )
}

export default App