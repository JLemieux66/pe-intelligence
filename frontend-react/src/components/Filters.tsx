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
  const [searchExact, setSearchExact] = useState(false)
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
  const [isPublic, setIsPublic] = useState<boolean | undefined>(undefined)

  // Filter operators
  const [filterOperator, setFilterOperator] = useState<'AND' | 'OR'>('AND')
  const [peFirmOperator, setPeFirmOperator] = useState<'AND' | 'OR'>('OR')
  const [industryGroupOperator, setIndustryGroupOperator] = useState<'AND' | 'OR'>('OR')
  const [industrySectorOperator, setIndustrySectorOperator] = useState<'AND' | 'OR'>('OR')
  const [verticalsOperator, setVerticalsOperator] = useState<'AND' | 'OR'>('OR')
  const [countryOperator, setCountryOperator] = useState<'AND' | 'OR'>('OR')
  const [stateOperator, setStateOperator] = useState<'AND' | 'OR'>('OR')
  const [cityOperator, setCityOperator] = useState<'AND' | 'OR'>('OR')

  // Fetch location data
  const { data: locationsData } = useLocations()

  // Apply filters automatically whenever any filter changes
  useEffect(() => {
    const filters: CompanyFilters = {}
    if (search) {
      filters.search = search
      filters.search_exact = searchExact
    }
    if (selectedFirms.length > 0) {
      filters.pe_firm = selectedFirms.join(',') // Multi-select: comma-separated
      filters.pe_firm_operator = peFirmOperator
    }
    if (selectedStatuses.length > 0) filters.status = selectedStatuses[0]
    if (selectedExitTypes.length > 0) filters.exit_type = selectedExitTypes[0]
    if (selectedIndustryGroups.length > 0) {
      filters.industry_group = selectedIndustryGroups.join(',')
      filters.industry_group_operator = industryGroupOperator
    }
    if (selectedIndustrySectors.length > 0) {
      filters.industry_sector = selectedIndustrySectors.join(',')
      filters.industry_sector_operator = industrySectorOperator
    }
    if (selectedVerticals.length > 0) {
      filters.verticals = selectedVerticals.join(',')
      filters.verticals_operator = verticalsOperator
    }
    if (selectedCountries.length > 0) {
      filters.country = selectedCountries.join(',')
      filters.country_operator = countryOperator
    }
    if (selectedStates.length > 0) {
      filters.state_region = selectedStates.join(',')
      filters.state_region_operator = stateOperator
    }
    if (selectedCities.length > 0) {
      filters.city = selectedCities.join(',')
      filters.city_operator = cityOperator
    }
    if (minRevenue) filters.min_revenue = parseFloat(minRevenue)
    if (maxRevenue) filters.max_revenue = parseFloat(maxRevenue)
    if (minEmployees) filters.min_employees = parseInt(minEmployees)
    if (maxEmployees) filters.max_employees = parseInt(maxEmployees)
    if (isPublic !== undefined) filters.is_public = isPublic

    // Set global filter operator
    filters.filter_operator = filterOperator

    onFilterChange(filters)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, searchExact, selectedFirms, selectedStatuses, selectedExitTypes, selectedIndustryGroups, selectedIndustrySectors, selectedVerticals, selectedCountries, selectedStates, selectedCities, minRevenue, maxRevenue, minEmployees, maxEmployees, isPublic, filterOperator, peFirmOperator, industryGroupOperator, industrySectorOperator, verticalsOperator, countryOperator, stateOperator, cityOperator])

  const toggleSelection = (value: string, currentList: string[], setter: (list: string[]) => void) => {
    if (currentList.includes(value)) {
      setter(currentList.filter(item => item !== value))
    } else {
      setter([...currentList, value])
    }
  }

  const handleReset = () => {
    setSearch('')
    setSearchExact(false)
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
    setIsPublic(undefined)
    setFilterOperator('AND')
    setPeFirmOperator('OR')
    setIndustryGroupOperator('OR')
    setIndustrySectorOperator('OR')
    setVerticalsOperator('OR')
    setCountryOperator('OR')
    setStateOperator('OR')
    setCityOperator('OR')
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

  // Reusable operator toggle component
  const OperatorToggle = ({ value, onChange, label }: { value: 'AND' | 'OR', onChange: (val: 'AND' | 'OR') => void, label?: string }) => (
    <div className="flex items-center gap-1 mt-1">
      {label && <span className="text-xs text-gray-500 mr-1">{label}:</span>}
      <button
        onClick={() => onChange('OR')}
        className={`px-2 py-0.5 text-xs font-medium rounded transition-colors ${
          value === 'OR'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        OR
      </button>
      <button
        onClick={() => onChange('AND')}
        className={`px-2 py-0.5 text-xs font-medium rounded transition-colors ${
          value === 'AND'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        AND
      </button>
    </div>
  )

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
        {/* Global Filter Operator */}
        <div className="pt-4 pb-2 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-600">Combine filters with:</span>
            <OperatorToggle value={filterOperator} onChange={setFilterOperator} />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {filterOperator === 'AND' ? 'Match ALL filter conditions' : 'Match ANY filter condition'}
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-900 bg-gray-50 hover:bg-white transition-colors placeholder:text-gray-400"
          />
          {search && (
            <label className="flex items-center mt-2 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={searchExact}
                onChange={(e) => setSearchExact(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              Exact match only
            </label>
          )}
        </div>

        {/* Multi-select PE Firms */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">PE Firms</label>
            {selectedFirms.length > 1 && (
              <OperatorToggle value={peFirmOperator} onChange={setPeFirmOperator} />
            )}
          </div>
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

        {/* Public Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company Type</label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                checked={isPublic === undefined}
                onChange={() => setIsPublic(undefined)}
                className="border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">All Companies</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                checked={isPublic === true}
                onChange={() => setIsPublic(true)}
                className="border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Public Only</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                checked={isPublic === false}
                onChange={() => setIsPublic(false)}
                className="border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Private Only</span>
            </label>
          </div>
        </div>

        {/* PitchBook Industry Groups */}
        {industryGroups.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Industry Group</label>
              {selectedIndustryGroups.length > 1 && (
                <OperatorToggle value={industryGroupOperator} onChange={setIndustryGroupOperator} />
              )}
            </div>
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
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Industry Sector</label>
              {selectedIndustrySectors.length > 1 && (
                <OperatorToggle value={industrySectorOperator} onChange={setIndustrySectorOperator} />
              )}
            </div>
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
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Verticals</label>
              {selectedVerticals.length > 1 && (
                <OperatorToggle value={verticalsOperator} onChange={setVerticalsOperator} />
              )}
            </div>
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
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-gray-600">Country</label>
                {selectedCountries.length > 1 && (
                  <OperatorToggle value={countryOperator} onChange={setCountryOperator} />
                )}
              </div>
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
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-gray-600">
                  State/Region
                  {selectedCountries.length > 0 && (
                    <span className="ml-1 text-xs text-emerald-600">
                      (in {selectedCountries.join(', ')})
                    </span>
                  )}
                </label>
                {selectedStates.length > 1 && (
                  <OperatorToggle value={stateOperator} onChange={setStateOperator} />
                )}
              </div>
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
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-gray-600">
                  City (Top 100)
                  {selectedStates.length > 0 && (
                    <span className="ml-1 text-xs text-emerald-600">
                      (in {selectedStates.join(', ')})
                    </span>
                  )}
                </label>
                {selectedCities.length > 1 && (
                  <OperatorToggle value={cityOperator} onChange={setCityOperator} />
                )}
              </div>
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