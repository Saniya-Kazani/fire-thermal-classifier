// src/components/CategoryLegend.jsx
// The legend: one row per category, showing its color, name and how many
// sites belong to it. Clicking a row switches that category on or off.
// It receives the on/off memory and the toggle function from App.jsx.

import { CATEGORIES, SITES } from '../data/mockData'

function CategoryLegend({ activeCategories, onToggle }) {
  return (
    <div className="rounded-lg bg-slate-700/50 p-3">
      <h2 className="text-sm font-semibold mb-1">Categories</h2>
      <p className="text-xs text-slate-400 mb-3">Click a category to show or hide it on the map.</p>

      <div className="space-y-1">
        {Object.entries(CATEGORIES).map(([key, cat]) => {
          const isOn = activeCategories[key]
          const count = SITES.filter((site) => site.category === key).length

          return (
            <button
              key={key}
              onClick={() => onToggle(key)}
              className={`flex items-center gap-2 w-full text-left text-sm px-2 py-1.5 rounded hover:bg-slate-600 ${
                isOn ? '' : 'opacity-40'
              }`}
            >
              <span
                className="inline-block w-3 h-3 rounded-full"
                style={{ backgroundColor: cat.color }}
              />
              <span className="flex-1">{cat.label}</span>
              <span className="text-xs text-slate-400">{count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default CategoryLegend