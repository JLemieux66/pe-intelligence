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
  const [searchExact, setSearchExact] = useState(false)
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

  // NOT operators (negation)
  const [peFirmNot, setPeFirmNot] = useState(false)
  const [industryGroupNot, setIndustryGroupNot] = useState(false)
  const [industrySectorNot, setIndustrySectorNot] = useState(false)
  const [verticalsNot, setVerticalsNot] = useState(false)
  const [countryNot, setCountryNot] = useState(false)
  const [stateNot, setStateNot] = useState(false)
  const [cityNot, setCityNot] = useState(false)

  // Data quality filters
  const [hasLinkedIn, setHasLinkedIn] = useState<boolean | undefined>(undefined)
  const [hasWebsite, setHasWebsite] = useState<boolean | undefined>(undefined)
  const [hasRevenue, setHasRevenue] = useState<boolean | undefined>(undefined)
  const [hasEmployees, setHasEmployees] = useState<boolean | undefined>(undefined)
  const [hasDescription, setHasDescription] = useState<boolean | undefined>(undefined)

  // Date range filters
  const [foundedYearMin, setFoundedYearMin] = useState('')
  const [foundedYearMax, setFoundedYearMax] = useState('')
  const [investmentYearMin, setInvestmentYearMin] = useState('')
  const [investmentYearMax, setInvestmentYearMax] = useState('')

  // Saved filter presets
  const [savedPresets, setSavedPresets] = useState<Array<{name: string, filters: any}>>(() => {
    const saved = localStorage.getItem('filterPresets')
    return saved ? JSON.parse(saved) : []
  })
  const [presetName, setPresetName] = useState('')

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
    if (search) {
      filters.search = search
      filters.search_exact = searchExact
    }
    if (selectedFirms.length > 0) {
      filters.pe_firm = selectedFirms.join(',')
      filters.pe_firm_operator = peFirmOperator
      filters.pe_firm_not = peFirmNot
    }
    if (selectedStatus) filters.status = selectedStatus
    if (selectedIndustryGroups.length > 0) {
      filters.industry_group = selectedIndustryGroups.join(',')
      filters.industry_group_operator = industryGroupOperator
      filters.industry_group_not = industryGroupNot
    }
    if (selectedIndustrySectors.length > 0) {
      filters.industry_sector = selectedIndustrySectors.join(',')
      filters.industry_sector_operator = industrySectorOperator
      filters.industry_sector_not = industrySectorNot
    }
    if (selectedVerticals.length > 0) {
      filters.verticals = selectedVerticals.join(',')
      filters.verticals_operator = verticalsOperator
      filters.verticals_not = verticalsNot
    }
    if (selectedCountries.length > 0) {
      filters.country = selectedCountries.join(',')
      filters.country_operator = countryOperator
      filters.country_not = countryNot
    }
    if (selectedStates.length > 0) {
      filters.state_region = selectedStates.join(',')
      filters.state_region_operator = stateOperator
      filters.state_region_not = stateNot
    }
    if (selectedCities.length > 0) {
      filters.city = selectedCities.join(',')
      filters.city_operator = cityOperator
      filters.city_not = cityNot
    }
    if (minRevenue) filters.min_revenue = parseFloat(minRevenue)
    if (maxRevenue) filters.max_revenue = parseFloat(maxRevenue)
    if (minEmployees) filters.min_employees = parseInt(minEmployees)
    if (maxEmployees) filters.max_employees = parseInt(maxEmployees)
    if (isPublic !== undefined) filters.is_public = isPublic

    // Data quality filters
    if (hasLinkedIn !== undefined) filters.has_linkedin_url = hasLinkedIn
    if (hasWebsite !== undefined) filters.has_website = hasWebsite
    if (hasRevenue !== undefined) filters.has_revenue = hasRevenue
    if (hasEmployees !== undefined) filters.has_employees = hasEmployees
    if (hasDescription !== undefined) filters.has_description = hasDescription

    // Date range filters
    if (foundedYearMin) filters.founded_year_min = parseInt(foundedYearMin)
    if (foundedYearMax) filters.founded_year_max = parseInt(foundedYearMax)
    if (investmentYearMin) filters.investment_year_min = parseInt(investmentYearMin)
    if (investmentYearMax) filters.investment_year_max = parseInt(investmentYearMax)

    // Global filter operator
    filters.filter_operator = filterOperator

    console.log('HorizontalFilters - Applying filters:', filters)
    onFilterChange(filters)
  }, [search, searchExact, selectedFirms, selectedStatus, selectedIndustryGroups, selectedIndustrySectors, selectedVerticals, selectedCountries, selectedStates, selectedCities, minRevenue, maxRevenue, minEmployees, maxEmployees, isPublic, filterOperator, peFirmOperator, industryGroupOperator, industrySectorOperator, verticalsOperator, countryOperator, stateOperator, cityOperator, peFirmNot, industryGroupNot, industrySectorNot, verticalsNot, countryNot, stateNot, cityNot, hasLinkedIn, hasWebsite, hasRevenue, hasEmployees, hasDescription, foundedYearMin, foundedYearMax, investmentYearMin, investmentYearMax, onFilterChange])

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
    setSearchExact(false)
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
    setIsPublic(undefined)
    setFilterOperator('AND')
    setPeFirmOperator('OR')
    setIndustryGroupOperator('OR')
    setIndustrySectorOperator('OR')
    setVerticalsOperator('OR')
    setCountryOperator('OR')
    setStateOperator('OR')
    setCityOperator('OR')
    setPeFirmNot(false)
    setIndustryGroupNot(false)
    setIndustrySectorNot(false)
    setVerticalsNot(false)
    setCountryNot(false)
    setStateNot(false)
    setCityNot(false)
    setHasLinkedIn(undefined)
    setHasWebsite(undefined)
    setHasRevenue(undefined)
    setHasEmployees(undefined)
    setHasDescription(undefined)
    setFoundedYearMin('')
    setFoundedYearMax('')
    setInvestmentYearMin('')
    setInvestmentYearMax('')
  }

  // Preset management functions
  const saveCurrentFilters = () => {
    if (!presetName.trim()) {
      alert('Please enter a name for this preset')
      return
    }

    const currentFilters = {
      search, searchExact, selectedFirms, selectedStatus,
      selectedIndustryGroups, selectedIndustrySectors, selectedVerticals,
      selectedCountries, selectedStates, selectedCities,
      minRevenue, maxRevenue, minEmployees, maxEmployees, isPublic,
      filterOperator, peFirmOperator, industryGroupOperator,
      industrySectorOperator, verticalsOperator, countryOperator,
      stateOperator, cityOperator, peFirmNot, industryGroupNot,
      industrySectorNot, verticalsNot, countryNot, stateNot, cityNot,
      hasLinkedIn, hasWebsite, hasRevenue, hasEmployees, hasDescription,
      foundedYearMin, foundedYearMax, investmentYearMin, investmentYearMax
    }

    const newPresets = [...savedPresets, { name: presetName, filters: currentFilters }]
    setSavedPresets(newPresets)
    localStorage.setItem('filterPresets', JSON.stringify(newPresets))
    setPresetName('')
    setOpenDropdown(null)
    alert(`Filter preset "${presetName}" saved!`)
  }

  const loadPreset = (preset: {name: string, filters: any}) => {
    const f = preset.filters
    setSearch(f.search || '')
    setSearchExact(f.searchExact || false)
    setSelectedFirms(f.selectedFirms || [])
    setSelectedStatus(f.selectedStatus || '')
    setSelectedIndustryGroups(f.selectedIndustryGroups || [])
    setSelectedIndustrySectors(f.selectedIndustrySectors || [])
    setSelectedVerticals(f.selectedVerticals || [])
    setSelectedCountries(f.selectedCountries || [])
    setSelectedStates(f.selectedStates || [])
    setSelectedCities(f.selectedCities || [])
    setMinRevenue(f.minRevenue || '')
    setMaxRevenue(f.maxRevenue || '')
    setMinEmployees(f.minEmployees || '')
    setMaxEmployees(f.maxEmployees || '')
    setIsPublic(f.isPublic)
    setFilterOperator(f.filterOperator || 'AND')
    setPeFirmOperator(f.peFirmOperator || 'OR')
    setIndustryGroupOperator(f.industryGroupOperator || 'OR')
    setIndustrySectorOperator(f.industrySectorOperator || 'OR')
    setVerticalsOperator(f.verticalsOperator || 'OR')
    setCountryOperator(f.countryOperator || 'OR')
    setStateOperator(f.stateOperator || 'OR')
    setCityOperator(f.cityOperator || 'OR')
    setPeFirmNot(f.peFirmNot || false)
    setIndustryGroupNot(f.industryGroupNot || false)
    setIndustrySectorNot(f.industrySectorNot || false)
    setVerticalsNot(f.verticalsNot || false)
    setCountryNot(f.countryNot || false)
    setStateNot(f.stateNot || false)
    setCityNot(f.cityNot || false)
    setHasLinkedIn(f.hasLinkedIn)
    setHasWebsite(f.hasWebsite)
    setHasRevenue(f.hasRevenue)
    setHasEmployees(f.hasEmployees)
    setHasDescription(f.hasDescription)
    setFoundedYearMin(f.foundedYearMin || '')
    setFoundedYearMax(f.foundedYearMax || '')
    setInvestmentYearMin(f.investmentYearMin || '')
    setInvestmentYearMax(f.investmentYearMax || '')
    setOpenDropdown(null)
  }

  const deletePreset = (presetName: string) => {
    if (confirm(`Delete preset "${presetName}"?`)) {
      const newPresets = savedPresets.filter(p => p.name !== presetName)
      setSavedPresets(newPresets)
      localStorage.setItem('filterPresets', JSON.stringify(newPresets))
    }
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

  // Reusable operator toggle component
  const OperatorToggle = ({ value, onChange }: { value: 'AND' | 'OR', onChange: (val: 'AND' | 'OR') => void }) => (
    <div className="flex items-center gap-1 bg-gray-100 rounded-md p-0.5">
      <button
        onClick={() => onChange('OR')}
        className={`px-2 py-1 text-xs font-semibold rounded transition-colors ${
          value === 'OR'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-800'
        }`}
      >
        OR
      </button>
      <button
        onClick={() => onChange('AND')}
        className={`px-2 py-1 text-xs font-semibold rounded transition-colors ${
          value === 'AND'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-800'
        }`}
      >
        AND
      </button>
    </div>
  )

  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-30">
      {/* Global Operator Bar */}
      <div className="px-6 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-gray-700">Combine Filters:</span>
            <OperatorToggle value={filterOperator} onChange={setFilterOperator} />
            <span className="text-xs text-gray-600">
              {filterOperator === 'AND' ? '(Match ALL conditions)' : '(Match ANY condition)'}
            </span>
          </div>
          {activeFilterCount > 0 && (
            <button
              onClick={handleReset}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
            >
              <X className="w-3 h-3" />
              Clear All ({activeFilterCount})
            </button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="px-6 py-4">
        <div className="flex items-center gap-3 flex-wrap">
          {/* Search */}
          <div className="flex-1 min-w-[240px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search companies..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white text-gray-900 placeholder:text-gray-400"
              />
            </div>
            {search && (
              <label className="flex items-center mt-1 text-xs text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={searchExact}
                  onChange={(e) => setSearchExact(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-1.5"
                />
                Exact match only
              </label>
            )}
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
                  {/* Operator Toggle - Only show when items selected */}
                  {selectedFirms.length > 0 && (
                    <div className="p-3 border-b border-gray-200 bg-blue-50">
                      <div className="flex items-center gap-3 flex-wrap">
                        {selectedFirms.length >= 2 && (
                          <>
                            <span className="text-xs font-medium text-gray-700">Match:</span>
                            <OperatorToggle value={peFirmOperator} onChange={setPeFirmOperator} />
                            <span className="text-xs text-gray-600">
                              {peFirmOperator === 'AND' ? 'ALL selected firms' : 'ANY selected firm'}
                            </span>
                            <span className="text-gray-300">|</span>
                          </>
                        )}
                        <label className="flex items-center gap-1.5 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={peFirmNot}
                            onChange={(e) => setPeFirmNot(e.target.checked)}
                            className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                          />
                          <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                        </label>
                      </div>
                    </div>
                  )}
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
                    {/* Operator Toggle - Only show when items selected */}
                    {selectedIndustrySectors.length > 0 && (
                      <div className="p-3 border-b border-gray-200 bg-purple-50">
                        <div className="flex items-center gap-3 flex-wrap">
                          {selectedIndustrySectors.length >= 2 && (
                            <>
                              <span className="text-xs font-medium text-gray-700">Match:</span>
                              <OperatorToggle value={industrySectorOperator} onChange={setIndustrySectorOperator} />
                              <span className="text-xs text-gray-600">
                                {industrySectorOperator === 'AND' ? 'ALL selected sectors' : 'ANY selected sector'}
                              </span>
                              <span className="text-gray-300">|</span>
                            </>
                          )}
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={industrySectorNot}
                              onChange={(e) => setIndustrySectorNot(e.target.checked)}
                              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                          </label>
                        </div>
                      </div>
                    )}
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
                    {/* Operator Toggle - Only show when items selected */}
                    {selectedIndustryGroups.length > 0 && (
                      <div className="p-3 border-b border-gray-200 bg-indigo-50">
                        <div className="flex items-center gap-3 flex-wrap">
                          {selectedIndustryGroups.length >= 2 && (
                            <>
                              <span className="text-xs font-medium text-gray-700">Match:</span>
                              <OperatorToggle value={industryGroupOperator} onChange={setIndustryGroupOperator} />
                              <span className="text-xs text-gray-600">
                                {industryGroupOperator === 'AND' ? 'ALL selected groups' : 'ANY selected group'}
                              </span>
                              <span className="text-gray-300">|</span>
                            </>
                          )}
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={industryGroupNot}
                              onChange={(e) => setIndustryGroupNot(e.target.checked)}
                              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                          </label>
                        </div>
                      </div>
                    )}
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
                    {/* Operator Toggle - Only show when items selected */}
                    {selectedVerticals.length > 0 && (
                      <div className="p-3 border-b border-gray-200 bg-pink-50">
                        <div className="flex items-center gap-3 flex-wrap">
                          {selectedVerticals.length >= 2 && (
                            <>
                              <span className="text-xs font-medium text-gray-700">Match:</span>
                              <OperatorToggle value={verticalsOperator} onChange={setVerticalsOperator} />
                              <span className="text-xs text-gray-600">
                                {verticalsOperator === 'AND' ? 'ONLY these verticals (exact match)' : 'ANY of these verticals'}
                              </span>
                              <span className="text-gray-300">|</span>
                            </>
                          )}
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={verticalsNot}
                              onChange={(e) => setVerticalsNot(e.target.checked)}
                              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                          </label>
                        </div>
                      </div>
                    )}
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
                    {/* Operator Toggle - Only show when items selected */}
                    {selectedCountries.length > 0 && (
                      <div className="p-3 border-b border-gray-200 bg-emerald-50">
                        <div className="flex items-center gap-3 flex-wrap">
                          {selectedCountries.length >= 2 && (
                            <>
                              <span className="text-xs font-medium text-gray-700">Match:</span>
                              <OperatorToggle value={countryOperator} onChange={setCountryOperator} />
                              <span className="text-xs text-gray-600">
                                {countryOperator === 'AND' ? 'ALL selected countries' : 'ANY selected country'}
                              </span>
                              <span className="text-gray-300">|</span>
                            </>
                          )}
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={countryNot}
                              onChange={(e) => setCountryNot(e.target.checked)}
                              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                          </label>
                        </div>
                      </div>
                    )}
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
                    {/* Operator Toggle - Only show when items selected */}
                    {selectedStates.length > 0 && (
                      <div className="p-3 border-b border-gray-200 bg-teal-50">
                        <div className="flex items-center gap-3 flex-wrap">
                          {selectedStates.length >= 2 && (
                            <>
                              <span className="text-xs font-medium text-gray-700">Match:</span>
                              <OperatorToggle value={stateOperator} onChange={setStateOperator} />
                              <span className="text-xs text-gray-600">
                                {stateOperator === 'AND' ? 'ALL selected states' : 'ANY selected state'}
                              </span>
                              <span className="text-gray-300">|</span>
                            </>
                          )}
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={stateNot}
                              onChange={(e) => setStateNot(e.target.checked)}
                              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                          </label>
                        </div>
                      </div>
                    )}
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
                    {/* Operator Toggle - Only show when items selected */}
                    {selectedCities.length > 0 && (
                      <div className="p-3 border-b border-gray-200 bg-cyan-50">
                        <div className="flex items-center gap-3 flex-wrap">
                          {selectedCities.length >= 2 && (
                            <>
                              <span className="text-xs font-medium text-gray-700">Match:</span>
                              <OperatorToggle value={cityOperator} onChange={setCityOperator} />
                              <span className="text-xs text-gray-600">
                                {cityOperator === 'AND' ? 'ALL selected cities' : 'ANY selected city'}
                              </span>
                              <span className="text-gray-300">|</span>
                            </>
                          )}
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={cityNot}
                              onChange={(e) => setCityNot(e.target.checked)}
                              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs font-medium text-red-700">NOT (Exclude)</span>
                          </label>
                        </div>
                      </div>
                    )}
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

          {/* Data Quality Dropdown */}
          <div className="relative">
            <button
              onClick={() => setOpenDropdown(openDropdown === 'data_quality' ? null : 'data_quality')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
            >
              <span>
                Data Quality {(hasLinkedIn !== undefined || hasWebsite !== undefined || hasRevenue !== undefined || hasEmployees !== undefined || hasDescription !== undefined) && (
                  <span className="ml-1 px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">•</span>
                )}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'data_quality' && (
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
                  className="absolute top-full left-0 mt-1 w-72 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
                >
                  <div className="p-4 space-y-3">
                    <div className="text-xs font-semibold text-gray-700 mb-2">Filter by data availability:</div>

                    {['LinkedIn URL', 'Website', 'Revenue', 'Employees', 'Description'].map((label, idx) => {
                      const states = [
                        [hasLinkedIn, setHasLinkedIn],
                        [hasWebsite, setHasWebsite],
                        [hasRevenue, setHasRevenue],
                        [hasEmployees, setHasEmployees],
                        [hasDescription, setHasDescription]
                      ][idx] as [boolean | undefined, (val: boolean | undefined) => void]

                      return (
                        <div key={label} className="flex items-center justify-between py-1">
                          <span className="text-sm text-gray-700">{label}:</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => states[1](undefined)}
                              className={`px-3 py-1 text-xs rounded ${
                                states[0] === undefined
                                  ? 'bg-gray-200 text-gray-800 font-medium'
                                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                              }`}
                            >
                              Any
                            </button>
                            <button
                              onClick={() => states[1](true)}
                              className={`px-3 py-1 text-xs rounded ${
                                states[0] === true
                                  ? 'bg-green-100 text-green-800 font-medium'
                                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                              }`}
                            >
                              Has
                            </button>
                            <button
                              onClick={() => states[1](false)}
                              className={`px-3 py-1 text-xs rounded ${
                                states[0] === false
                                  ? 'bg-red-100 text-red-800 font-medium'
                                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                              }`}
                            >
                              Missing
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Date Ranges Dropdown */}
          <div className="relative">
            <button
              onClick={() => setOpenDropdown(openDropdown === 'dates' ? null : 'dates')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[120px] justify-between"
            >
              <span>
                Dates {(foundedYearMin || foundedYearMax || investmentYearMin || investmentYearMax) && (
                  <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs">•</span>
                )}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'dates' && (
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
                  className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
                >
                  <div className="p-4 space-y-4">
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">Founded Year</div>
                      <div className="grid grid-cols-2 gap-2">
                        <label className="block">
                          <span className="text-xs text-gray-600">Min</span>
                          <input
                            type="number"
                            placeholder="1990"
                            value={foundedYearMin}
                            onChange={(e) => setFoundedYearMin(e.target.value)}
                            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          />
                        </label>
                        <label className="block">
                          <span className="text-xs text-gray-600">Max</span>
                          <input
                            type="number"
                            placeholder="2024"
                            value={foundedYearMax}
                            onChange={(e) => setFoundedYearMax(e.target.value)}
                            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          />
                        </label>
                      </div>
                    </div>

                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">Investment Year</div>
                      <div className="grid grid-cols-2 gap-2">
                        <label className="block">
                          <span className="text-xs text-gray-600">Min</span>
                          <input
                            type="number"
                            placeholder="2015"
                            value={investmentYearMin}
                            onChange={(e) => setInvestmentYearMin(e.target.value)}
                            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          />
                        </label>
                        <label className="block">
                          <span className="text-xs text-gray-600">Max</span>
                          <input
                            type="number"
                            placeholder="2024"
                            value={investmentYearMax}
                            onChange={(e) => setInvestmentYearMax(e.target.value)}
                            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          />
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Saved Filters Dropdown */}
          <div className="relative">
            <button
              onClick={() => setOpenDropdown(openDropdown === 'saved_filters' ? null : 'saved_filters')}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 min-w-[140px] justify-between"
            >
              <span>
                Saved Filters {savedPresets.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                    {savedPresets.length}
                  </span>
                )}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {openDropdown === 'saved_filters' && (
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
                  className="absolute top-full left-0 mt-1 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-y-auto"
                >
                  <div className="p-4">
                    {/* Save current filters */}
                    <div className="mb-4 pb-4 border-b border-gray-200">
                      <div className="text-xs font-semibold text-gray-700 mb-2">Save Current Filters</div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Preset name..."
                          value={presetName}
                          onChange={(e) => setPresetName(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && saveCurrentFilters()}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        />
                        <button
                          onClick={saveCurrentFilters}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                        >
                          Save
                        </button>
                      </div>
                    </div>

                    {/* Load saved presets */}
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">Saved Presets</div>
                      {savedPresets.length === 0 ? (
                        <div className="text-sm text-gray-500 text-center py-4">
                          No saved presets yet
                        </div>
                      ) : (
                        <div className="space-y-1">
                          {savedPresets.map((preset) => (
                            <div
                              key={preset.name}
                              className="flex items-center justify-between px-3 py-2 hover:bg-gray-50 rounded group"
                            >
                              <button
                                onClick={() => loadPreset(preset)}
                                className="flex-1 text-left text-sm text-gray-700 hover:text-blue-600"
                              >
                                {preset.name}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  deletePreset(preset.name)
                                }}
                                className="ml-2 text-red-600 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
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
