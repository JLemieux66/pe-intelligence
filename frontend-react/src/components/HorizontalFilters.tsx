import { useState, useEffect } from 'react'
import { Search, X, ChevronDown } from 'lucide-react'
import type { PEFirm, CompanyFilters } from '../types/company'
import { useLocations, usePitchBookMetadata } from '../hooks/useCompanies'

interface HorizontalFiltersProps {
  peFirms: PEFirm[]
  peFirmsLoading?: boolean
  onFilterChange: (filters: CompanyFilters) => void
}

export default function HorizontalFilters({ peFirms, peFirmsLoading, onFilterChange }: HorizontalFiltersProps) {
  const [search, setSearch] = useState('')
  const [selectedFirms, setSelectedFirms] = useState<string[]>([])
  const [selectedStatus, setSelectedStatus] = useState<string>('')
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
  
  // Dropdown open states
  const [openDropdown, setOpenDropdown] = useState<string | null>(null)

  console.log('HorizontalFilters render - openDropdown:', openDropdown)

  // Fetch location data
  const { data: locationsData } = useLocations()
  
  // Fetch PitchBook metadata (all industry groups, sectors, verticals)
  const { data: pitchBookData } = usePitchBookMetadata()

  // Use PitchBook metadata from API instead of calculating from filtered investments
  const industryGroups = pitchBookData?.industry_groups || []
  const industrySectors = pitchBookData?.industry_sectors || []
  const verticals = pitchBookData?.verticals || []

  // Apply filters automatically whenever any filter changes
  useEffect(() => {
    const filters: CompanyFilters = {}
    if (search) filters.search = search
    if (selectedFirms.length > 0) filters.pe_firm = selectedFirms.join(',')
    if (selectedStatus) filters.status = selectedStatus
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
    
    console.log('HorizontalFilters - Applying filters:', filters)
    onFilterChange(filters)
  }, [search, selectedFirms, selectedStatus, selectedIndustryGroups, selectedIndustrySectors, selectedVerticals, selectedCountries, selectedStates, selectedCities, minRevenue, maxRevenue, minEmployees, maxEmployees, onFilterChange])

  const toggleSelection = (value: string, currentList: string[], setter: (list: string[]) => void) => {
    console.log('toggleSelection called', value, 'openDropdown:', openDropdown)
    if (currentList.includes(value)) {
      setter(currentList.filter(item => item !== value))
    } else {
      setter([...currentList, value])
    }
  }

  const handleReset = () => {
    setSearch('')
    setSelectedFirms([])
    setSelectedStatus('')
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

  const activeFilterCount = [
    selectedFirms.length > 0,
    selectedStatus !== '',
    selectedIndustryGroups.length > 0,
    selectedIndustrySectors.length > 0,
    selectedVerticals.length > 0,
    selectedCountries.length > 0,
    selectedStates.length > 0,
    selectedCities.length > 0,
    minRevenue !== '',
    maxRevenue !== '',
    minEmployees !== '',
    maxEmployees !== ''
  ].filter(Boolean).length

  // Filter states by selected countries
  const filteredStates = locationsData?.states.filter(
    state => selectedCountries.length === 0 || selectedCountries.includes(state.country || '')
  ) || []

  // Filter cities by selected states and countries
  const filteredCities = locationsData?.cities.filter(city => {
    if (selectedStates.length > 0 && !selectedStates.includes(city.state || '')) return false
    if (selectedCountries.length > 0 && !selectedCountries.includes(city.country || '')) return false
    return true
  }) || []

  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-30">
      {/* Filter Bar */}
      <div className="px-6 py-4">
        <div className="flex items-center gap-3 flex-wrap">
          {/* Search */}
          <div className="relative flex-1 min-w-[240px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white text-gray-900 placeholder:text-gray-400"
            />
          </div>

          {/* PE Firms Dropdown */}
          <div className="relative">
            <button 
              onClick={() => setOpenDropdown(openDropdown === 'firms' ? null : 'firms')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
            >
              <span>
                PE Firms {selectedFirms.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                    {selectedFirms.length}
                  </span>
                )}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'firms' && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={(e) => {
                    if (e.target === e.currentTarget) {
                      setOpenDropdown(null);
                    }
                  }} 
                />
                <div 
                  className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                >
                  <div className="p-2 space-y-1">
                    {peFirmsLoading ? (
                      <div className="px-3 py-8 text-center text-sm text-gray-500">
                        Loading PE firms...
                      </div>
                    ) : peFirms.length === 0 ? (
                      <div className="px-3 py-8 text-center text-sm text-gray-500">
                        No PE firms found
                      </div>
                    ) : (
                      peFirms.map((firm) => (
                        <label 
                          key={firm.id} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedFirms.includes(firm.name)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(firm.name, selectedFirms, setSelectedFirms);
                            }}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-3 text-sm text-gray-700 flex-1">{firm.name}</span>
                          <span className="text-xs text-gray-500">({firm.total_investments})</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Status Dropdown */}
          <div className="relative">
            <button 
              onClick={() => setOpenDropdown(openDropdown === 'status' ? null : 'status')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[120px] justify-between"
            >
              <span>{selectedStatus || 'Status'}</span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'status' && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={(e) => {
                    if (e.target === e.currentTarget) {
                      setOpenDropdown(null);
                    }
                  }} 
                />
                <div 
                  className="absolute top-full left-0 mt-1 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
                >
                  <div className="p-2">
                    <button
                      onClick={() => { setSelectedStatus(''); setOpenDropdown(null); }}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${!selectedStatus ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'}`}
                    >
                      All
                    </button>
                    <button
                      onClick={() => { setSelectedStatus('Active'); setOpenDropdown(null); }}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${selectedStatus === 'Active' ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'}`}
                    >
                      Active
                    </button>
                    <button
                      onClick={() => { setSelectedStatus('Exit'); setOpenDropdown(null); }}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${selectedStatus === 'Exit' ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'}`}
                    >
                      Exit
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Industry Sector Dropdown */}
          {industrySectors.length > 0 && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === 'industry_sector' ? null : 'industry_sector')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
              >
                <span>
                  Industry Sector {selectedIndustrySectors.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                      {selectedIndustrySectors.length}
                    </span>
                  )}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {openDropdown === 'industry_sector' && (
                <>
                  {console.log('Rendering industry_sector dropdown, sectors:', industrySectors.length)}
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        setOpenDropdown(null);
                      }
                    }} 
                  />
                  <div 
                    className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  >
                    <div className="p-2 space-y-1">
                      {industrySectors.map((sector) => (
                        <label 
                          key={sector} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedIndustrySectors.includes(sector)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(sector, selectedIndustrySectors, setSelectedIndustrySectors);
                            }}
                            className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                          />
                          <span className="ml-3 text-sm text-gray-700">{sector}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Industry Group Dropdown */}
          {industryGroups.length > 0 && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === 'industry_group' ? null : 'industry_group')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
              >
                <span>
                  Industry Group {selectedIndustryGroups.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs">
                      {selectedIndustryGroups.length}
                    </span>
                  )}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {openDropdown === 'industry_group' && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        setOpenDropdown(null);
                      }
                    }} 
                  />
                  <div 
                    className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  >
                    <div className="p-2 space-y-1">
                      {industryGroups.map((group) => (
                        <label 
                          key={group} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedIndustryGroups.includes(group)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(group, selectedIndustryGroups, setSelectedIndustryGroups);
                            }}
                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="ml-3 text-sm text-gray-700">{group}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Verticals Dropdown */}
          {verticals.length > 0 && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === 'verticals' ? null : 'verticals')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[120px] justify-between"
              >
                <span>
                  Verticals {selectedVerticals.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-pink-100 text-pink-700 rounded text-xs">
                      {selectedVerticals.length}
                    </span>
                  )}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {openDropdown === 'verticals' && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        setOpenDropdown(null);
                      }
                    }} 
                  />
                  <div 
                    className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  >
                    <div className="p-2 space-y-1">
                      {verticals.map((vertical) => (
                        <label 
                          key={vertical} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedVerticals.includes(vertical)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(vertical, selectedVerticals, setSelectedVerticals);
                            }}
                            className="rounded border-gray-300 text-pink-600 focus:ring-pink-500"
                          />
                          <span className="ml-3 text-sm text-gray-700">{vertical}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Country Dropdown */}
          {locationsData && locationsData.countries.length > 0 && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === 'country' ? null : 'country')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
              >
                <span>
                  Country {selectedCountries.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded text-xs">
                      {selectedCountries.length}
                    </span>
                  )}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {openDropdown === 'country' && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        setOpenDropdown(null);
                      }
                    }} 
                  />
                  <div 
                    className="absolute top-full left-0 mt-1 w-72 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  >
                    <div className="p-2 space-y-1">
                      {locationsData.countries.map((country) => (
                        <label 
                          key={country.name} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedCountries.includes(country.name)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(country.name, selectedCountries, setSelectedCountries);
                            }}
                            className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                          />
                          <span className="ml-3 text-sm text-gray-700 flex-1">{country.name}</span>
                          <span className="text-xs text-gray-500">({country.count})</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* State/Region Dropdown */}
          {filteredStates.length > 0 && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === 'state' ? null : 'state')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
              >
                <span>
                  State/Region {selectedStates.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded text-xs">
                      {selectedStates.length}
                    </span>
                  )}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {openDropdown === 'state' && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        setOpenDropdown(null);
                      }
                    }}
                  />
                  <div 
                    className="absolute top-full left-0 mt-1 w-72 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  >
                    <div className="p-2 space-y-1">
                      {filteredStates.map((state) => (
                        <label 
                          key={`${state.name}-${state.country}`} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedStates.includes(state.name)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(state.name, selectedStates, setSelectedStates);
                            }}
                            className="rounded border-gray-300 text-teal-600 focus:ring-teal-500"
                          />
                          <span className="ml-3 text-sm text-gray-700 flex-1">
                            {state.name}
                            {state.country && selectedCountries.length === 0 && (
                              <span className="text-xs text-gray-500 ml-1">({state.country})</span>
                            )}
                          </span>
                          <span className="text-xs text-gray-500">({state.count})</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* City Dropdown */}
          {filteredCities.length > 0 && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === 'city' ? null : 'city')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[120px] justify-between"
              >
                <span>
                  City {selectedCities.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-cyan-100 text-cyan-700 rounded text-xs">
                      {selectedCities.length}
                    </span>
                  )}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {openDropdown === 'city' && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={(e) => {
                      if (e.target === e.currentTarget) {
                        setOpenDropdown(null);
                      }
                    }} 
                  />
                  <div 
                    className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  >
                    <div className="p-2 space-y-1">
                      {filteredCities.slice(0, 100).map((city) => (
                        <label 
                          key={`${city.name}-${city.state}-${city.country}`} 
                          className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedCities.includes(city.name)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelection(city.name, selectedCities, setSelectedCities);
                            }}
                            className="rounded border-gray-300 text-cyan-600 focus:ring-cyan-500"
                          />
                          <span className="ml-3 text-sm text-gray-700 flex-1">
                            {city.name}
                            {(city.state || city.country) && (
                              <span className="text-xs text-gray-500 ml-1">
                                ({[city.state, selectedStates.length === 0 && selectedCountries.length === 0 ? city.country : null].filter(Boolean).join(', ')})
                              </span>
                            )}
                          </span>
                          <span className="text-xs text-gray-500">({city.count})</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Revenue Range */}
          <div className="relative">
            <button 
              onClick={() => setOpenDropdown(openDropdown === 'revenue' ? null : 'revenue')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[120px] justify-between"
            >
              <span>
                Revenue {(minRevenue || maxRevenue) && (
                  <span className="ml-1 px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">•</span>
                )}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'revenue' && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={(e) => {
                    if (e.target === e.currentTarget) {
                      setOpenDropdown(null);
                    }
                  }} 
                />
                <div 
                  className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
                >
                  <div className="p-4 space-y-3">
                    <label className="block">
                      <span className="text-xs font-medium text-gray-700">Min Revenue (M$)</span>
                      <input
                        type="number"
                        placeholder="0"
                        value={minRevenue}
                        onChange={(e) => setMinRevenue(e.target.value)}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </label>
                    <label className="block">
                      <span className="text-xs font-medium text-gray-700">Max Revenue (M$)</span>
                      <input
                        type="number"
                        placeholder="∞"
                        value={maxRevenue}
                        onChange={(e) => setMaxRevenue(e.target.value)}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </label>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Employees Range */}
          <div className="relative">
            <button 
              onClick={() => setOpenDropdown(openDropdown === 'employees' ? null : 'employees')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
            >
              <span>
                Employees {(minEmployees || maxEmployees) && (
                  <span className="ml-1 px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">•</span>
                )}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'employees' && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={(e) => {
                    if (e.target === e.currentTarget) {
                      setOpenDropdown(null);
                    }
                  }} 
                />
                <div 
                  className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
                >
                  <div className="p-4 space-y-3">
                    <label className="block">
                      <span className="text-xs font-medium text-gray-700">Min Employees</span>
                      <input
                        type="number"
                        placeholder="0"
                        value={minEmployees}
                        onChange={(e) => setMinEmployees(e.target.value)}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </label>
                    <label className="block">
                      <span className="text-xs font-medium text-gray-700">Max Employees</span>
                      <input
                        type="number"
                        placeholder="∞"
                        value={maxEmployees}
                        onChange={(e) => setMaxEmployees(e.target.value)}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </label>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Clear Filters */}
          {activeFilterCount > 0 && (
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2 transition-colors"
            >
              <X className="w-4 h-4" />
              Clear ({activeFilterCount})
            </button>
          )}
        </div>
      </div>

      {/* Active Filter Tags */}
      {activeFilterCount > 0 && (
        <div className="px-6 pb-3 flex flex-wrap gap-2">
          {/* PE Firms */}
          {selectedFirms.map((firm) => (
            <span key={firm} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {firm}
              <button
                onClick={() => toggleSelection(firm, selectedFirms, setSelectedFirms)}
                className="ml-1.5 hover:text-blue-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* Status */}
          {selectedStatus && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
              Status: {selectedStatus}
              <button
                onClick={() => setSelectedStatus('')}
                className="ml-1.5 hover:text-slate-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          
          {/* Industry Sectors */}
          {selectedIndustrySectors.map((sector) => (
            <span key={sector} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {sector}
              <button
                onClick={() => toggleSelection(sector, selectedIndustrySectors, setSelectedIndustrySectors)}
                className="ml-1.5 hover:text-purple-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* Industry Groups */}
          {selectedIndustryGroups.map((group) => (
            <span key={group} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
              {group}
              <button
                onClick={() => toggleSelection(group, selectedIndustryGroups, setSelectedIndustryGroups)}
                className="ml-1.5 hover:text-indigo-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* Verticals */}
          {selectedVerticals.map((vertical) => (
            <span key={vertical} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-pink-100 text-pink-800">
              {vertical}
              <button
                onClick={() => toggleSelection(vertical, selectedVerticals, setSelectedVerticals)}
                className="ml-1.5 hover:text-pink-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* Countries */}
          {selectedCountries.map((country) => (
            <span key={country} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
              🌍 {country}
              <button
                onClick={() => toggleSelection(country, selectedCountries, setSelectedCountries)}
                className="ml-1.5 hover:text-emerald-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* States */}
          {selectedStates.map((state) => (
            <span key={state} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-teal-100 text-teal-800">
              📍 {state}
              <button
                onClick={() => toggleSelection(state, selectedStates, setSelectedStates)}
                className="ml-1.5 hover:text-teal-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* Cities */}
          {selectedCities.map((city) => (
            <span key={city} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-100 text-cyan-800">
              🏙️ {city}
              <button
                onClick={() => toggleSelection(city, selectedCities, setSelectedCities)}
                className="ml-1.5 hover:text-cyan-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          {/* Revenue Range */}
          {(minRevenue || maxRevenue) && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              Revenue: {minRevenue || '0'}M - {maxRevenue || '∞'}M
              <button
                onClick={() => { setMinRevenue(''); setMaxRevenue(''); }}
                className="ml-1.5 hover:text-purple-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          
          {/* Employee Range */}
          {(minEmployees || maxEmployees) && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
              Employees: {minEmployees || '0'} - {maxEmployees || '∞'}
              <button
                onClick={() => { setMinEmployees(''); setMaxEmployees(''); }}
                className="ml-1.5 hover:text-orange-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  )
}
