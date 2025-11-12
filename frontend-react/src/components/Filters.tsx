import { useState, useEffect, useMemo } from 'react'
import { Search, Filter, X, MapPin, Globe } from 'lucide-react'
import type { PEFirm, CompanyFilters, Investment } from '../types/company'
import { useLocations } from '../hooks/useCompanies'

interface FiltersProps {
  peFirms: PEFirm[]
  investments?: Investment[]
  onFilterChange: (filters: CompanyFilters) => void
}

export default function Filters({ peFirms, investments = [], onFilterChange }: FiltersProps) {
  const [search, setSearch] = useState('')
  const [searchMode, setSearchMode] = useState<'contains' | 'exact'>('contains')
  const [filterMode, setFilterMode] = useState<'any' | 'all'>('any')
  const [selectedFirms, setSelectedFirms] = useState<string[]>([])
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([])
  const [selectedExitTypes, setSelectedExitTypes] = useState<string[]>([])
  const [selectedIndustryGroups, setSelectedIndustryGroups] = useState<string[]>([])
  const [selectedIndustrySectors, setSelectedIndustrySectors] = useState<string[]>([])
  const [selectedVerticals, setSelectedVerticals] = useState<string[]>([])
  const [selectedCountries, setSelectedCountries] = useState<string[]>([])
  const [selectedStates, setSelectedStates] = useState<string[]>([])
  const [selectedCities, setSelectedCities] = useState<string[]>([])
  const [minRevenue, setMinRevenue] = useState('')
  const [maxRevenue, setMaxRevenue] = useState('')
  const [minEmployees, setMinEmployees] = useState('')
  const [maxEmployees, setMaxEmployees] = useState('')

  // Fetch location data
  const { data: locationsData } = useLocations()

  // Apply filters automatically whenever any filter changes
  useEffect(() => {
    const filters: CompanyFilters = {}
    if (search) filters.search = search
    filters.search_mode = searchMode
    filters.filter_mode = filterMode
    if (selectedFirms.length > 0) filters.pe_firm = selectedFirms.join(',') // Multi-select: comma-separated
    if (selectedStatuses.length > 0) filters.status = selectedStatuses[0]
    if (selectedExitTypes.length > 0) filters.exit_type = selectedExitTypes[0]
    if (selectedIndustryGroups.length > 0) filters.industry_group = selectedIndustryGroups.join(',')
    if (selectedIndustrySectors.length > 0) filters.industry_sector = selectedIndustrySectors.join(',')
    if (selectedVerticals.length > 0) filters.verticals = selectedVerticals.join(',')
    if (selectedCountries.length > 0) filters.country = selectedCountries.join(',')
    if (selectedStates.length > 0) filters.state_region = selectedStates.join(',')
    if (selectedCities.length > 0) filters.city = selectedCities.join(',')
    if (minRevenue) filters.min_revenue = parseFloat(minRevenue)
    if (maxRevenue) filters.max_revenue = parseFloat(maxRevenue)
    if (minEmployees) filters.min_employees = parseInt(minEmployees)
    if (maxEmployees) filters.max_employees = parseInt(maxEmployees)
    onFilterChange(filters)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, searchMode, filterMode, selectedFirms, selectedStatuses, selectedExitTypes, selectedIndustryGroups, selectedIndustrySectors, selectedVerticals, selectedCountries, selectedStates, selectedCities, minRevenue, maxRevenue, minEmployees, maxEmployees])

  const toggleSelection = (value: string, currentList: string[], setter: (list: string[]) => void) => {
    if (currentList.includes(value)) {
      setter(currentList.filter(item => item !== value))
    } else {
      setter([...currentList, value])
    }
  }

  const handleReset = () => {
    setSearch('')
    setSelectedFirms([])
    setSelectedStatuses([])
    setSelectedExitTypes([])
    setSelectedIndustryGroups([])
    setSelectedIndustrySectors([])
    setSelectedVerticals([])
    setSelectedCountries([])
    setSelectedStates([])
    setSelectedCities([])
    setMinRevenue('')
    setMaxRevenue('')
    setMinEmployees('')
    setMaxEmployees('')
  }

  const statuses = ['Active', 'Exit']
  const exitTypes = ['IPO', 'Acquisition']

  // Extract unique PitchBook values from investments
  const industryGroups = useMemo(() => {
    const groups = new Set<string>()
    investments.forEach(inv => {
      if (inv.primary_industry_group) groups.add(inv.primary_industry_group)
    })
    return Array.from(groups).sort()
  }, [investments])

  const industrySectors = useMemo(() => {
    const sectors = new Set<string>()
    investments.forEach(inv => {
      if (inv.primary_industry_sector) sectors.add(inv.primary_industry_sector)
    })
    return Array.from(sectors).sort()
  }, [investments])

  const verticals = useMemo(() => {
    const verts = new Set<string>()
    investments.forEach(inv => {
      if (inv.verticals) {
        inv.verticals.split(',').forEach(v => verts.add(v.trim()))
      }
    })
    return Array.from(verts).sort()
  }, [investments])

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-gray-100 sticky top-4 max-h-[calc(100vh-2rem)] flex flex-col">
      <div className="flex items-center justify-between p-5 pb-4 border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg mr-2 shadow-md shadow-blue-500/30">
            <Filter className="w-4 h-4 text-white" />
          </div>
          <h2 className="text-lg font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">Filters</h2>
        </div>
        <button
          onClick={handleReset}
          className="text-sm text-blue-600 hover:text-blue-700 font-semibold flex items-center transition-colors"
        >
          <X className="w-4 h-4 mr-1" />
          Clear
        </button>
      </div>
      
      <div className="space-y-4 overflow-y-auto p-5 pt-0">
        {/* Search */}
        <div className="space-y-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-900 bg-gray-50 hover:bg-white transition-colors placeholder:text-gray-400"
            />
          </div>
          {/* Search Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-600">Search:</span>
            <div className="flex items-center bg-gray-100 rounded-lg p-0.5 flex-1">
              <button
                onClick={() => setSearchMode('contains')}
                className={`flex-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                  searchMode === 'contains'
                    ? 'bg-white text-blue-700 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Contains
              </button>
              <button
                onClick={() => setSearchMode('exact')}
                className={`flex-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                  searchMode === 'exact'
                    ? 'bg-white text-blue-700 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Exact
              </button>
            </div>
          </div>
        </div>

        {/* Filter Mode Toggle */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-xs font-semibold text-gray-700">Multi-Select Mode</span>
          </div>
          <div className="flex items-center bg-white rounded-lg p-0.5 shadow-sm">
            <button
              onClick={() => setFilterMode('any')}
              className={`flex-1 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                filterMode === 'any'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-700 hover:text-gray-900'
              }`}
              title="Match ANY selected filter (OR logic)"
            >
              Match ANY
            </button>
            <button
              onClick={() => setFilterMode('all')}
              className={`flex-1 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                filterMode === 'all'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-700 hover:text-gray-900'
              }`}
              title="Match ALL selected filters (AND logic)"
            >
              Match ALL
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-2">
            {filterMode === 'any' ? '🔵 Shows companies matching ANY selected option' : '🟣 Shows companies matching ALL selected options'}
          </p>
        </div>

        {/* Multi-select PE Firms */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">PE Firms</label>
          <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto p-2 border border-gray-200 rounded-lg">
            {peFirms.map((firm) => (
              <button
                key={firm.id}
                onClick={() => toggleSelection(firm.name, selectedFirms, setSelectedFirms)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedFirms.includes(firm.name)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {firm.name} ({firm.total_investments})
              </button>
            ))}
          </div>
          {selectedFirms.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {selectedFirms.map((firm) => (
                <span key={firm} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {firm}
                  <button
                    onClick={() => toggleSelection(firm, selectedFirms, setSelectedFirms)}
                    className="ml-1 hover:text-blue-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <div className="space-y-2">
            {statuses.map((status) => (
              <label key={status} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedStatuses.includes(status)}
                  onChange={() => toggleSelection(status, selectedStatuses, setSelectedStatuses)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">{status}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Exit Types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Exit Type</label>
          <div className="space-y-2">
            {exitTypes.map((exitType) => (
              <label key={exitType} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedExitTypes.includes(exitType)}
                  onChange={() => toggleSelection(exitType, selectedExitTypes, setSelectedExitTypes)}
                  disabled={!selectedStatuses.includes('Exit')}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
                />
                <span className="ml-2 text-sm text-gray-700">{exitType}</span>
              </label>
            ))}
          </div>
        </div>

        {/* PitchBook Industry Groups */}
        {industryGroups.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Industry Group</label>
            <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded p-2">
              {industryGroups.map((group) => (
                <label key={group} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedIndustryGroups.includes(group)}
                    onChange={() => toggleSelection(group, selectedIndustryGroups, setSelectedIndustryGroups)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{group}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* PitchBook Industry Sectors */}
        {industrySectors.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Industry Sector</label>
            <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded p-2">
              {industrySectors.map((sector) => (
                <label key={sector} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedIndustrySectors.includes(sector)}
                    onChange={() => toggleSelection(sector, selectedIndustrySectors, setSelectedIndustrySectors)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{sector}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* PitchBook Verticals */}
        {verticals.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Verticals</label>
            <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded p-2">
              {verticals.map((vertical) => (
                <label key={vertical} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedVerticals.includes(vertical)}
                    onChange={() => toggleSelection(vertical, selectedVerticals, setSelectedVerticals)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{vertical}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Location Filters */}
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg p-3 space-y-3">
          <div className="flex items-center mb-2">
            <Globe className="w-4 h-4 text-emerald-600 mr-2" />
            <h3 className="text-sm font-semibold text-gray-800">Location</h3>
          </div>

          {/* Countries */}
          {locationsData && locationsData.countries.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Country</label>
              <div className="max-h-40 overflow-y-auto space-y-1.5 bg-white rounded p-2 border border-emerald-200">
                {locationsData.countries.map((country) => (
                  <label key={country.name} className="flex items-center justify-between hover:bg-emerald-50 px-1.5 py-0.5 rounded transition-colors">
                    <div className="flex items-center flex-1 min-w-0">
                      <input
                        type="checkbox"
                        checked={selectedCountries.includes(country.name)}
                        onChange={() => toggleSelection(country.name, selectedCountries, setSelectedCountries)}
                        className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 flex-shrink-0"
                      />
                      <span className="ml-2 text-sm text-gray-700 truncate">{country.name}</span>
                    </div>
                    <span className="text-xs text-gray-500 ml-2 flex-shrink-0">({country.count})</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* States/Regions - filtered by selected countries */}
          {locationsData && locationsData.states.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                State/Region
                {selectedCountries.length > 0 && (
                  <span className="ml-1 text-xs text-emerald-600">
                    (in {selectedCountries.join(', ')})
                  </span>
                )}
              </label>
              <div className="max-h-40 overflow-y-auto space-y-1.5 bg-white rounded p-2 border border-emerald-200">
                {locationsData.states
                  .filter(state => selectedCountries.length === 0 || selectedCountries.includes(state.country || ''))
                  .map((state) => (
                    <label key={`${state.name}-${state.country}`} className="flex items-center justify-between hover:bg-emerald-50 px-1.5 py-0.5 rounded transition-colors">
                      <div className="flex items-center flex-1 min-w-0">
                        <input
                          type="checkbox"
                          checked={selectedStates.includes(state.name)}
                          onChange={() => toggleSelection(state.name, selectedStates, setSelectedStates)}
                          className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 flex-shrink-0"
                        />
                        <span className="ml-2 text-sm text-gray-700 truncate">
                          {state.name}
                          {state.country && selectedCountries.length === 0 && (
                            <span className="text-xs text-gray-500 ml-1">({state.country})</span>
                          )}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 ml-2 flex-shrink-0">({state.count})</span>
                    </label>
                  ))}
              </div>
            </div>
          )}

          {/* Cities - filtered by selected states */}
          {locationsData && locationsData.cities.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                City (Top 100)
                {selectedStates.length > 0 && (
                  <span className="ml-1 text-xs text-emerald-600">
                    (in {selectedStates.join(', ')})
                  </span>
                )}
              </label>
              <div className="max-h-40 overflow-y-auto space-y-1.5 bg-white rounded p-2 border border-emerald-200">
                {locationsData.cities
                  .filter(city => {
                    if (selectedStates.length > 0 && !selectedStates.includes(city.state || '')) return false
                    if (selectedCountries.length > 0 && !selectedCountries.includes(city.country || '')) return false
                    return true
                  })
                  .map((city) => (
                    <label key={`${city.name}-${city.state}-${city.country}`} className="flex items-center justify-between hover:bg-emerald-50 px-1.5 py-0.5 rounded transition-colors">
                      <div className="flex items-center flex-1 min-w-0">
                        <input
                          type="checkbox"
                          checked={selectedCities.includes(city.name)}
                          onChange={() => toggleSelection(city.name, selectedCities, setSelectedCities)}
                          className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 flex-shrink-0"
                        />
                        <span className="ml-2 text-sm text-gray-700 truncate">
                          {city.name}
                          {(city.state || city.country) && (
                            <span className="text-xs text-gray-500 ml-1">
                              ({[city.state, selectedStates.length === 0 && selectedCountries.length === 0 ? city.country : null].filter(Boolean).join(', ')})
                            </span>
                          )}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 ml-2 flex-shrink-0">({city.count})</span>
                    </label>
                  ))}
              </div>
            </div>
          )}

          {/* Selected Location Tags */}
          {(selectedCountries.length > 0 || selectedStates.length > 0 || selectedCities.length > 0) && (
            <div className="flex flex-wrap gap-1.5 pt-2 border-t border-emerald-200">
              {selectedCountries.map((country) => (
                <span key={country} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                  <MapPin className="w-3 h-3 mr-0.5" />
                  {country}
                  <button
                    onClick={() => toggleSelection(country, selectedCountries, setSelectedCountries)}
                    className="ml-1 hover:text-emerald-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              {selectedStates.map((state) => (
                <span key={state} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-teal-100 text-teal-800">
                  {state}
                  <button
                    onClick={() => toggleSelection(state, selectedStates, setSelectedStates)}
                    className="ml-1 hover:text-teal-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              {selectedCities.map((city) => (
                <span key={city} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-cyan-100 text-cyan-800">
                  {city}
                  <button
                    onClick={() => toggleSelection(city, selectedCities, setSelectedCities)}
                    className="ml-1 hover:text-cyan-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Revenue Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Revenue (M$)</label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              placeholder="Min"
              value={minRevenue}
              onChange={(e) => setMinRevenue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <input
              type="number"
              placeholder="Max"
              value={maxRevenue}
              onChange={(e) => setMaxRevenue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
        </div>

        {/* Employee Count Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Employee Count</label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              placeholder="Min"
              value={minEmployees}
              onChange={(e) => setMinEmployees(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <input
              type="number"
              placeholder="Max"
              value={maxEmployees}
              onChange={(e) => setMaxEmployees(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
        </div>

      </div>
    </div>
  )
}