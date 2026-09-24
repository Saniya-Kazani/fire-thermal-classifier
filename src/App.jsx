// src/App.jsx
// The main page. It holds the "shared memory" (which site is selected,
// which categories are switched on) and lays out the screen.
// Layout: on a phone everything stacks in one scrolling column
// (header, summary, map, then the panels). On a large screen (lg:)
// the map sits on the left and the panels on the right.

import { useState } from 'react'
import { CATEGORIES, SITES, ALERTS } from './data/mockData'
import MapView from './components/MapView'
import CategoryLegend from './components/CategoryLegend'
import SiteDetailPanel from './components/SiteDetailPanel'
import AlertsFeed from './components/AlertsFeed'
import SummaryBar from './components/SummaryBar'

function App() {
  // Shared memory: which site is selected (null = none)
  const [selectedSiteId, setSelectedSiteId] = useState(null)

  // Shared memory: which categories are switched on (all start as true)
  const [activeCategories, setActiveCategories] = useState(
    Object.fromEntries(Object.keys(CATEGORIES).map((key) => [key, true]))
  )

  // Only the sites and alerts whose category is switched on
  const visibleSites = SITES.filter((site) => activeCategories[site.category])
  const visibleAlerts = ALERTS.filter((alert) => activeCategories[alert.category])
  const selectedSite = SITES.find((site) => site.id === selectedSiteId)

  // Flip one category on/off
  function toggleCategory(key) {
    setActiveCategories({ ...activeCategories, [key]: !activeCategories[key] })
  }

  return (
    <div className="min-h-screen lg:h-screen flex flex-col bg-slate-900 text-white">
      {/* Top bar */}
      <header className="px-4 py-3 bg-slate-800 border-b border-slate-700">
        <h1 className="text-base sm:text-lg font-bold">
          Industrial Fire & Thermal Source Classification
        </h1>
        <p className="text-xs text-slate-400">Demo region: Panipat, Haryana</p>
      </header>

      {/* Key numbers (they follow the category filter) */}
      <SummaryBar sites={visibleSites} alerts={visibleAlerts} />

      <main className="flex flex-col lg:flex-row flex-1 lg:min-h-0">
        {/* Map: fixed height on phones, fills the left side on large screens */}
        <section className="relative h-[55vh] lg:h-auto lg:flex-1">
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
          />

          <SiteDetailPanel
            site={selectedSite}
            onClose={() => setSelectedSiteId(null)}
          />

          <AlertsFeed
            alerts={visibleAlerts}
            selectedSiteId={selectedSiteId}
            onSelectSite={setSelectedSiteId}
          />
        </aside>
      </main>
    </div>
  )
}

export default App