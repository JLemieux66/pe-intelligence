import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import type { Investment as InvestmentType } from '../types/company';

interface Company {
  id: number;
  name: string;
  website?: string;
  linkedin_url?: string;
  crunchbase_url?: string;
  description?: string;
  headquarters?: string;
  industry_category?: string;
  revenue_range?: string;
  employee_count?: string;
  is_public?: boolean;
  stock_exchange?: string;
  status?: string;
  exit_type?: string;
  verticals?: string;
}

type Investment = InvestmentType;

interface CompanyEditModalProps {
  company: Company;
  investment?: Investment;  // Optional: if editing from investment view
  onClose: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://peportco-production.up.railway.app/api';

export default function CompanyEditModal({ company, investment, onClose }: CompanyEditModalProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'basic' | 'pitchbook' | 'investment'>('basic');

  // Fetch all investments for this company
  const { data: investments = [], isLoading: investmentsLoading, error: investmentsError } = useQuery<Investment[]>({
    queryKey: ['company-investments', company.id],
    queryFn: async () => {
      console.log('Fetching investments for company:', company.id);
      const response = await fetch(`${API_BASE_URL}/companies/${company.id}/investments`);
      if (!response.ok) {
        console.error('Failed to fetch investments:', response.status);
        throw new Error('Failed to fetch investments');
      }
      const data = await response.json();
      console.log('Investments fetched:', data);
      return data;
    }
  });

  // Log investments state
  useEffect(() => {
    console.log('Investments state updated:', investments);
    console.log('Loading:', investmentsLoading);
    console.log('Error:', investmentsError);
  }, [investments, investmentsLoading, investmentsError]);

  // Track investment form data for each PE firm
  const [investmentForms, setInvestmentForms] = useState<Record<number, Investment>>({});

  // Initialize investment forms when investments load
  useEffect(() => {
    if (investments.length > 0) {
      const forms: Record<number, Investment> = {};
      investments.forEach(inv => {
        forms[inv.investment_id] = { ...inv };
      });
      setInvestmentForms(forms);
    }
  }, [investments]);

  // Multi-select states for PitchBook fields
  const [selectedIndustryGroups, setSelectedIndustryGroups] = useState<string[]>(
    (company as any).primary_industry_group ? [(company as any).primary_industry_group] : []
  );
  const [selectedIndustrySectors, setSelectedIndustrySectors] = useState<string[]>(
    (company as any).primary_industry_sector ? [(company as any).primary_industry_sector] : []
  );
  const [selectedVerticals, setSelectedVerticals] = useState<string[]>(
    (company as any).verticals ? (company as any).verticals.split(',').map((v: string) => v.trim()) : []
  );

  // Parse headquarters into city, state, country
  const parseHeadquarters = (hq?: string) => {
    if (!hq) return { city: '', state_region: '', country: '' };
    const parts = hq.split(',').map(p => p.trim());
    if (parts.length === 3) {
      return { city: parts[0], state_region: parts[1], country: parts[2] };
    } else if (parts.length === 2) {
      return { city: parts[0], state_region: '', country: parts[1] };
    } else if (parts.length === 1) {
      return { city: parts[0], state_region: '', country: '' };
    }
    return { city: '', state_region: '', country: '' };
  };

  const hqParts = parseHeadquarters(company.headquarters);

  const [formData, setFormData] = useState({
    name: company.name || '',
    website: company.website || '',
    linkedin_url: company.linkedin_url || '',
    crunchbase_url: company.crunchbase_url || '',
    description: company.description || '',
    city: hqParts.city,
    state_region: hqParts.state_region,
    country: hqParts.country,
    industry_category: company.industry_category || '',
    revenue_range: company.revenue_range || '',
    employee_count: company.employee_count || '',
    is_public: company.is_public || false,
    ipo_exchange: company.stock_exchange || '',
    // Investment fields (if provided)
    computed_status: investment?.status || company.status || '',
    exit_type: investment?.exit_type || company.exit_type || '',
    exit_year: investment?.exit_year || '',
    investment_year: investment?.investment_year || '',
    // PitchBook fields
    primary_industry_group: (company as any).primary_industry_group || '',
    primary_industry_sector: (company as any).primary_industry_sector || '',
    verticals: (company as any).verticals || '',
    current_revenue_usd: (company as any).current_revenue_usd || '',
    last_known_valuation_usd: (company as any).last_known_valuation_usd || '',
    hq_location: (company as any).hq_location || '',
    hq_country: (company as any).hq_country || '',
  });

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      console.log('Sending PUT request:', {
        url: `${API_BASE_URL}/companies/${company.id}`,
        data
      });

      const response = await fetch(`${API_BASE_URL}/companies/${company.id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response text:', errorText);
        let error;
        try {
          error = JSON.parse(errorText);
        } catch {
          error = { detail: errorText };
        }
        throw new Error(error.detail || 'Failed to update company');
      }

      const responseText = await response.text();
      console.log('Response text:', responseText);
      
      let result;
      try {
        result = JSON.parse(responseText);
        console.log('Update result:', result);
      } catch (e) {
        console.error('Failed to parse response:', e);
        throw new Error('Invalid response from server');
      }
      
      return result;
    },
    onSuccess: async () => {
      console.log('Mutation succeeded, invalidating queries...');
      
      // Invalidate the specific company query (for the modal)
      await queryClient.invalidateQueries({ 
        queryKey: ['company', company.id],
        refetchType: 'active'
      });
      
      // Invalidate and force refetch all company queries (for the table)
      await queryClient.invalidateQueries({ 
        queryKey: ['companies'],
        exact: false,
        refetchType: 'active'  // Force refetch active queries immediately
      });
      
      console.log('Queries invalidated, refetching...');
      
      // Also force refetch to ensure fresh data
      await queryClient.refetchQueries({
        queryKey: ['company', company.id]
      });
      
      await queryClient.refetchQueries({
        queryKey: ['companies'],
        exact: false,
        type: 'active'
      });
      
      console.log('Refetch complete');
      
      // Close modal after data is refreshed
      setTimeout(() => {
        onClose();
      }, 300);
    },
  });

  const updateInvestmentMutation = useMutation({
    mutationFn: async ({ investmentId, data }: { investmentId: number; data: any }) => {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      const response = await fetch(`${API_BASE_URL}/investments/${investmentId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let error;
        try {
          error = JSON.parse(errorText);
        } catch {
          error = { detail: errorText };
        }
        throw new Error(error.detail || 'Failed to update investment');
      }

      return response.json();
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ 
        queryKey: ['companies'],
        exact: false,
        refetchType: 'active'
      });
      await queryClient.invalidateQueries({ 
        queryKey: ['company-investments', company.id]
      });
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Separate company updates from investment updates
    const companyUpdates: any = {};
    const investmentUpdates: any = {};
    
    // Investment field keys
    const investmentFields = new Set(['computed_status', 'exit_type', 'exit_year', 'investment_year']);
    
    // Map form fields to company fields for comparison
    const fieldMap: Record<string, { companyKey: string; getValue: (c: Company) => any }> = {
      name: { companyKey: 'name', getValue: (c) => c.name || '' },
      website: { companyKey: 'website', getValue: (c) => c.website || '' },
      linkedin_url: { companyKey: 'linkedin_url', getValue: (c) => c.linkedin_url || '' },
      crunchbase_url: { companyKey: 'crunchbase_url', getValue: (c) => c.crunchbase_url || '' },
      description: { companyKey: 'description', getValue: (c) => c.description || '' },
      city: { companyKey: 'headquarters', getValue: (c) => parseHeadquarters(c.headquarters).city },
      state_region: { companyKey: 'headquarters', getValue: (c) => parseHeadquarters(c.headquarters).state_region },
      country: { companyKey: 'headquarters', getValue: (c) => parseHeadquarters(c.headquarters).country },
      industry_category: { companyKey: 'industry_category', getValue: (c) => c.industry_category || '' },
      revenue_range: { companyKey: 'revenue_range', getValue: (c) => c.revenue_range || '' },
      employee_count: { companyKey: 'employee_count', getValue: (c) => c.employee_count || '' },
      is_public: { companyKey: 'is_public', getValue: (c) => c.is_public || false },
      ipo_exchange: { companyKey: 'stock_exchange', getValue: (c) => c.stock_exchange || '' },
    };
    
    // Check for changes
    Object.keys(formData).forEach((key) => {
      const typedKey = key as keyof typeof formData;
      const newValue = formData[typedKey];
      
      // Handle investment fields separately
      if (investmentFields.has(key) && investment) {
        const originalValue = (investment as any)[key] || '';
        if (newValue !== originalValue) {
          investmentUpdates[key] = newValue;
        }
      } else {
        // Handle company fields
        const mapping = fieldMap[key];
        if (mapping) {
          const originalValue = mapping.getValue(company);
          if (newValue !== originalValue) {
            companyUpdates[key] = newValue;
          }
        }
      }
    });

    // Handle multi-select PitchBook fields
    const newIndustryGroup = selectedIndustryGroups.join(', ');
    const originalIndustryGroup = (company as any).primary_industry_group || '';
    if (newIndustryGroup !== originalIndustryGroup) {
      companyUpdates.primary_industry_group = newIndustryGroup;
    }

    const newIndustrySector = selectedIndustrySectors.join(', ');
    const originalIndustrySector = (company as any).primary_industry_sector || '';
    if (newIndustrySector !== originalIndustrySector) {
      companyUpdates.primary_industry_sector = newIndustrySector;
    }

    const newVerticals = selectedVerticals.join(', ');
    const originalVerticals = (company as any).verticals || '';
    if (newVerticals !== originalVerticals) {
      companyUpdates.verticals = newVerticals;
    }

    // Submit both updates if needed
    let hasUpdates = false;
    
    if (Object.keys(companyUpdates).length > 0) {
      hasUpdates = true;
      await updateMutation.mutateAsync(companyUpdates);
    }
    
    if (Object.keys(investmentUpdates).length > 0 && investment?.investment_id) {
      hasUpdates = true;
      await updateInvestmentMutation.mutateAsync(investmentUpdates);
    }
    
    if (!hasUpdates) {
      onClose();
    } else {
      setTimeout(() => onClose(), 300);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Edit Company</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 bg-gray-50 px-6">
          <div className="flex space-x-8">
            <button
              type="button"
              onClick={() => setActiveTab('basic')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'basic'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Basic Info
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('pitchbook')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'pitchbook'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              PitchBook Data
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('investment')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'investment'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Investment Status
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Basic Info Tab */}
          {activeTab === 'basic' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Information</h3>
              
              {/* Company Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Company Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                />
                <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{company.name}</span></p>
              </div>

              {/* URLs Section */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Links & Profiles
                </h4>

                {/* Website */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Website
                  </label>
                  <input
                    type="url"
                    name="website"
                    value={formData.website}
                    onChange={handleChange}
                    placeholder="https://example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                  />
                  <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{company.website || 'Not set'}</span></p>
                </div>

                {/* LinkedIn URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    LinkedIn URL
                  </label>
                  <input
                    type="url"
                    name="linkedin_url"
                    value={formData.linkedin_url}
                    onChange={handleChange}
                    placeholder="https://linkedin.com/company/example"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                  />
                  <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{company.linkedin_url || 'Not set'}</span></p>
                </div>

                {/* Crunchbase URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Crunchbase URL
                  </label>
                  <input
                    type="url"
                    name="crunchbase_url"
                    value={formData.crunchbase_url}
                    onChange={handleChange}
                    placeholder="https://www.crunchbase.com/organization/example"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                  />
                  <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{company.crunchbase_url || 'Not set'}</span></p>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none bg-white text-gray-900 placeholder-gray-400"
                  placeholder="Brief description of the company..."
                />
                {company.description && (
                  <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{company.description.slice(0, 80)}{company.description.length > 80 ? '...' : ''}</span></p>
                )}
              </div>

              {/* Location Section */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 space-y-4">
                <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Headquarters
                </h4>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      HQ Location
                    </label>
                    <input
                      type="text"
                      name="hq_location"
                      value={formData.hq_location}
                      onChange={handleChange}
                      placeholder="San Francisco, CA"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                    />
                    <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{(company as any).hq_location || 'Not set'}</span></p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      HQ Country
                    </label>
                    <input
                      type="text"
                      name="hq_country"
                      value={formData.hq_country}
                      onChange={handleChange}
                      placeholder="United States"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                    />
                    <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{(company as any).hq_country || 'Not set'}</span></p>
                  </div>
                </div>
              </div>

              {/* Public Company Status */}
              <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="is_public"
                      checked={formData.is_public}
                      onChange={handleChange}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700">Publicly Traded (IPO)</span>
                  </label>
                  {formData.is_public && (
                    <input
                      type="text"
                      name="ipo_exchange"
                      value={formData.ipo_exchange}
                      onChange={handleChange}
                      placeholder="NYSE, NASDAQ, etc."
                      className="flex-1 ml-4 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                    />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* PitchBook Data Tab */}
          {activeTab === 'pitchbook' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">PitchBook Enrichment Data</h3>
            
              {/* Industry Group - Multi-select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Industry Group
                </label>
                <div className="flex flex-wrap gap-2 p-3 border border-gray-300 rounded-md max-h-60 overflow-y-auto">
                  {['Software', 'IT Services', 'Healthcare Services', 'Financial Services', 'Commercial Services', 
                    'Consumer Services', 'Media', 'Commercial Products', 'Consumer Products', 'Energy', 
                    'Materials & Resources', 'Other'].map((group) => (
                    <button
                      key={group}
                      type="button"
                      onClick={() => {
                        if (selectedIndustryGroups.includes(group)) {
                          setSelectedIndustryGroups(selectedIndustryGroups.filter(g => g !== group));
                        } else {
                          setSelectedIndustryGroups([...selectedIndustryGroups, group]);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                        selectedIndustryGroups.includes(group)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {group}
                    </button>
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-500">Current: {(company as any).primary_industry_group || 'Not set'}</p>
              </div>

              {/* Industry Sector - Multi-select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Industry Sector
                </label>
                <div className="flex flex-wrap gap-2 p-3 border border-gray-300 rounded-md max-h-60 overflow-y-auto">
                  {['B2B', 'B2C', 'Information Technology', 'Healthcare', 'Financials', 'Consumer Discretionary',
                    'Consumer Staples', 'Industrials', 'Communication Services', 'Energy', 'Materials', 
                    'Real Estate', 'Utilities'].map((sector) => (
                    <button
                      key={sector}
                      type="button"
                      onClick={() => {
                        if (selectedIndustrySectors.includes(sector)) {
                          setSelectedIndustrySectors(selectedIndustrySectors.filter(s => s !== sector));
                        } else {
                          setSelectedIndustrySectors([...selectedIndustrySectors, sector]);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                        selectedIndustrySectors.includes(sector)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {sector}
                    </button>
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-500">Current: {(company as any).primary_industry_sector || 'Not set'}</p>
              </div>

              {/* Verticals - Multi-select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Verticals
                </label>
                <div className="flex flex-wrap gap-2 p-3 border border-gray-300 rounded-md max-h-60 overflow-y-auto">
                  {['SaaS', 'Enterprise Software', 'Cloud Computing', 'Cybersecurity', 'Fintech', 'E-commerce',
                    'Healthcare IT', 'AI/ML', 'Data Analytics', 'Digital Marketing', 'MarTech', 'AdTech',
                    'IoT', 'Blockchain', 'DevOps', 'Business Intelligence', 'CRM', 'ERP', 'HR Tech',
                    'Legal Tech', 'Real Estate Tech', 'EdTech', 'Supply Chain', 'Other'].map((vertical) => (
                    <button
                      key={vertical}
                      type="button"
                      onClick={() => {
                        if (selectedVerticals.includes(vertical)) {
                          setSelectedVerticals(selectedVerticals.filter(v => v !== vertical));
                        } else {
                          setSelectedVerticals([...selectedVerticals, vertical]);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                        selectedVerticals.includes(vertical)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {vertical}
                    </button>
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-500">Current: {(company as any).verticals || 'Not set'}</p>
              </div>

              {/* Revenue and Valuation */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Current Revenue (M USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="current_revenue_usd"
                    value={formData.current_revenue_usd}
                    onChange={handleChange}
                    placeholder="e.g., 150.5"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Current: {(company as any).current_revenue_usd ? `$${(company as any).current_revenue_usd}M` : 'Not set'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valuation (M USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="last_known_valuation_usd"
                    value={formData.last_known_valuation_usd}
                    onChange={handleChange}
                    placeholder="e.g., 500"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Current: {(company as any).last_known_valuation_usd ? `$${(company as any).last_known_valuation_usd}M` : 'Not set'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Investment Status Tab */}
          {activeTab === 'investment' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">PE Firm Investments</h3>
                {!investmentsLoading && !investmentsError && investments.length > 0 && (
                  <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                    {investments.length} {investments.length === 1 ? 'Investment' : 'Investments'}
                  </span>
                )}
              </div>
              
              {investmentsLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                    <p className="text-gray-500 text-sm">Loading investments...</p>
                  </div>
                </div>
              )}
              
              {investmentsError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-700 text-sm font-medium">Error loading investments</p>
                  <p className="text-red-600 text-xs mt-1">{investmentsError.message}</p>
                </div>
              )}
              
              {!investmentsLoading && !investmentsError && investments.length === 0 && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-gray-600 text-sm font-medium">No PE firm investments recorded</p>
                  <p className="text-gray-500 text-xs mt-1">Investment relationships will appear here once added</p>
                </div>
              )}
              
              {!investmentsLoading && !investmentsError && investments.length > 0 && (
                <div className="space-y-4">
                  {investments.map((inv) => (
                  <div key={inv.investment_id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200 rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-base text-gray-900">
                          {inv.pe_firm_name}
                        </h4>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          inv.status === 'Active' 
                            ? 'bg-green-100 text-green-800' 
                            : inv.status === 'Exit'
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {inv.status}
                        </span>
                      </div>
                    </div>
                    
                    <div className="p-4 space-y-4">
                      {/* Status */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                          Investment Status
                        </label>
                        <select
                          value={investmentForms[inv.investment_id]?.status || inv.status}
                          onChange={(e) => {
                            setInvestmentForms(prev => ({
                              ...prev,
                              [inv.investment_id]: {
                                ...prev[inv.investment_id],
                                status: e.target.value
                              }
                            }));
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900"
                        >
                          <option value="">Select Status</option>
                          <option value="Active">Active</option>
                          <option value="Exit">Exit</option>
                        </select>
                        <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{inv.status}</span></p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        {/* Investment Year */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Investment Year
                          </label>
                          <input
                            type="text"
                            value={investmentForms[inv.investment_id]?.investment_year || inv.investment_year || ''}
                            onChange={(e) => {
                              setInvestmentForms(prev => ({
                                ...prev,
                                [inv.investment_id]: {
                                  ...prev[inv.investment_id],
                                  investment_year: e.target.value
                                }
                              }));
                            }}
                            placeholder="e.g., 2020"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                          />
                          <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{inv.investment_year || 'Not set'}</span></p>
                        </div>

                        {/* Exit Year */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            Exit Year
                          </label>
                          <input
                            type="text"
                            value={investmentForms[inv.investment_id]?.exit_year || inv.exit_year || ''}
                            onChange={(e) => {
                              setInvestmentForms(prev => ({
                                ...prev,
                                [inv.investment_id]: {
                                  ...prev[inv.investment_id],
                                  exit_year: e.target.value
                                }
                              }));
                            }}
                            placeholder="e.g., 2024"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900 placeholder-gray-400"
                          />
                          <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{inv.exit_year || 'Not set'}</span></p>
                        </div>
                      </div>

                      {/* Exit Type */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                          Exit Type
                        </label>
                        <select
                          value={investmentForms[inv.investment_id]?.exit_type || inv.exit_type || ''}
                          onChange={(e) => {
                            setInvestmentForms(prev => ({
                              ...prev,
                              [inv.investment_id]: {
                                ...prev[inv.investment_id],
                                exit_type: e.target.value
                              }
                            }));
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-gray-900"
                        >
                          <option value="">None</option>
                          <option value="IPO">IPO</option>
                          <option value="Acquisition">Acquisition</option>
                          <option value="Secondary Sale">Secondary Sale</option>
                          <option value="Buyout">Buyout</option>
                          <option value="Merger">Merger</option>
                          <option value="Other">Other</option>
                        </select>
                        <p className="mt-1.5 text-xs text-gray-500">Current: <span className="font-medium">{inv.exit_type || 'Not set'}</span></p>
                      </div>

                      {/* Update Button for this investment */}
                      <div className="pt-2">
                        <button
                          type="button"
                          onClick={async () => {
                            const updates = investmentForms[inv.investment_id];
                            if (updates && inv.investment_id) {
                              await updateInvestmentMutation.mutateAsync({
                                investmentId: inv.investment_id,
                                data: updates
                              });
                            }
                          }}
                          disabled={updateInvestmentMutation.isPending}
                          className="w-full px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow"
                        >
                          {updateInvestmentMutation.isPending ? (
                            <span className="flex items-center justify-center">
                              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Updating...
                            </span>
                          ) : (
                            `Update ${inv.pe_firm_name} Investment`
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {updateMutation.isError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {updateMutation.error instanceof Error ? updateMutation.error.message : 'Failed to update company'}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            {/* Show Save button for Basic Info and PitchBook tabs (company-level data) */}
            {(activeTab === 'basic' || activeTab === 'pitchbook') && (
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
              >
                {updateMutation.isPending ? 'Saving...' : 'Save Company Changes'}
              </button>
            )}
            
            {/* For Investment tab, just show close button (each investment has its own update button) */}
            <button
              type="button"
              onClick={onClose}
              className={`${activeTab === 'investment' ? 'flex-1' : 'flex-1'} bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors`}
            >
              {activeTab === 'investment' ? 'Close' : 'Cancel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
