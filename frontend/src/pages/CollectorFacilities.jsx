import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassInput,
  Navbar, 
  LoadingState, 
  EmptyState 
} from '../components'

export function CollectorFacilities() {
  const { user } = useAuth()
  const [allFacilities, setAllFacilities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  // Define facility categories based on facility_type and waste_categories
  const categories = [
    { id: 'medical', label: 'MEDICAL WASTE', description: 'Incinerators / biomedical waste facilities', icon: '🏥' },
    { id: 'dry', label: 'DRY WASTE', description: 'Dumpyards / landfill facilities', icon: '🗑️' },
    { id: 'wet', label: 'WET WASTE', description: 'Wastewater treatment plants', icon: '💧' },
    { id: 'recyclable', label: 'RECYCLABLE WASTE', description: 'Recycling / material recovery facilities', icon: '♻️' },
  ]

  useEffect(() => {
    fetchAllFacilities()
  }, [])

  const fetchAllFacilities = async () => {
    try {
      setLoading(true)
      setError('')
      // Fetch from the public facilities endpoint to get all facilities
      const response = await api.get('/facilities', { params: { limit: 500 } })
      setAllFacilities(response.data || [])
    } catch (err) {
      setError('Failed to load facilities')
    } finally {
      setLoading(false)
    }
  }

  // Categorize a facility based on its type and waste categories
  const categorizeFacility = (facility) => {
    const type = (facility.facility_type || '').toLowerCase()
    const categories_str = (facility.waste_categories || '').toLowerCase()
    
    // Medical waste facilities
    if (type.includes('biomedical') || type.includes('incinerator') || type.includes('medical') ||
        categories_str.includes('medical')) {
      return 'medical'
    }
    
    // Wet waste facilities
    if (type.includes('wet') || type.includes('wastewater') || type.includes('sewage') ||
        type.includes('treatment plant') || type.includes('compost') ||
        categories_str.includes('wet') || categories_str.includes('organic')) {
      return 'wet'
    }
    
    // Recyclable waste facilities
    if (type.includes('recycl') || type.includes('recovery') || type.includes('dwcc') ||
        type.includes('material recovery') || type.includes('mrp') ||
        categories_str.includes('plastic') || categories_str.includes('glass') || 
        categories_str.includes('metal') || categories_str.includes('paper') ||
        categories_str.includes('cardboard') || categories_str.includes('e-waste')) {
      return 'recyclable'
    }
    
    // Dry waste facilities (landfill, dumping ground, etc.)
    if (type.includes('landfill') || type.includes('dump') || type.includes('transfer') ||
        categories_str.includes('dry')) {
      return 'dry'
    }
    
    // Default to dry waste
    return 'dry'
  }

  // Filter and group facilities
  const getFilteredFacilities = () => {
    let filtered = allFacilities
    
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(f => 
        (f.facility_name || '').toLowerCase().includes(term) ||
        (f.facility_type || '').toLowerCase().includes(term) ||
        (f.area_name || '').toLowerCase().includes(term) ||
        (f.city || '').toLowerCase().includes(term)
      )
    }
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(f => categorizeFacility(f) === selectedCategory)
    }
    
    return filtered
  }

  const groupedFacilities = () => {
    const filtered = getFilteredFacilities()
    const groups = {}
    
    categories.forEach(cat => {
      groups[cat.id] = filtered.filter(f => categorizeFacility(f) === cat.id)
    })
    
    // Also include uncategorized
    const categorizedIds = new Set()
    Object.values(groups).flat().forEach(f => categorizedIds.add(f.id))
    const uncategorized = filtered.filter(f => !categorizedIds.has(f.id))
    if (uncategorized.length > 0) {
      groups['other'] = uncategorized
    }
    
    return groups
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'inactive': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    }
  }

  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading facilities..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container max-w-7xl">
          <EmptyState
            title="Unable to Load Facilities"
            description={error}
            action={{ label: 'Retry', onClick: fetchAllFacilities }}
          />
        </div>
      </div>
    )
  }

  const groups = groupedFacilities()

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Waste Facilities</h1>
          <p className="text-text-secondary mt-1">Facilities grouped by waste type purpose</p>
        </div>

        {/* Filters */}
        <GlassCard className="mb-8">
          <div className="flex flex-col sm:flex-row gap-4">
            <GlassInput
              label="Search Facilities"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, type, area, or city"
              className="flex-1"
            />
            <GlassInput
              label="Category"
              type="select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              options={[
                { value: 'all', label: 'All Categories' },
                ...categories.map(c => ({ value: c.id, label: c.label }))
              ]}
              className="sm:w-64"
            />
          </div>
        </GlassCard>

        {/* Facility Categories */}
        <div className="space-y-6">
          {categories.map(category => {
            const facilities = groups[category.id] || []
            return (
              <GlassCard key={category.id}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{category.icon}</span>
                    <div>
                      <h3 className="font-semibold text-text-primary">{category.label}</h3>
                      <p className="text-xs text-text-muted">{category.description}</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 bg-emerald/10 text-emerald rounded-full text-sm font-medium">
                    {facilities.length} facilities
                  </span>
                </div>

                {facilities.length === 0 ? (
                  <div className="text-center py-8 text-text-muted">
                    No facilities in this category
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-glass-border">
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Facility</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Type</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">City</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Waste Categories</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Capacity (kg/day)</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {facilities.map((facility) => (
                          <tr key={facility.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                            <td className="p-4 font-medium text-text-primary">{facility.facility_name}</td>
                            <td className="p-4 text-text-secondary">{facility.facility_type}</td>
                            <td className="p-4 text-text-secondary">{facility.area_name || 'N/A'}</td>
                            <td className="p-4 text-text-secondary">{facility.city || 'N/A'}</td>
                            <td className="p-4 text-text-secondary text-sm max-w-xs truncate">
                              {facility.waste_categories ? 
                                (() => {
                                  try {
                                    return JSON.parse(facility.waste_categories).join(', ')
                                  } catch {
                                    return facility.waste_categories
                                  }
                                })() 
                                : 'N/A'}
                            </td>
                            <td className="p-4 text-right text-text-secondary">
                              {facility.capacity_kg_per_day ? facility.capacity_kg_per_day.toLocaleString() : 'Unknown'}
                            </td>
                            <td className="p-4">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(facility.status)}`}>
                                {facility.status || 'Unknown'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </GlassCard>
            )
          })}
          
          {groups.other && groups.other.length > 0 && (
            <GlassCard>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📦</span>
                  <div>
                    <h3 className="font-semibold text-text-primary">Other Facilities</h3>
                    <p className="text-xs text-text-muted">Facilities not matching standard categories</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-emerald/10 text-emerald rounded-full text-sm font-medium">
                  {groups.other.length} facilities
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-glass-border">
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Facility</th>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Type</th>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">City</th>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Waste Categories</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">Capacity (kg/day)</th>
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.other.map((facility) => (
                      <tr key={facility.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                        <td className="p-4 font-medium text-text-primary">{facility.facility_name}</td>
                        <td className="p-4 text-text-secondary">{facility.facility_type}</td>
                        <td className="p-4 text-text-secondary">{facility.area_name || 'N/A'}</td>
                        <td className="p-4 text-text-secondary">{facility.city || 'N/A'}</td>
                        <td className="p-4 text-text-secondary text-sm max-w-xs truncate">
                          {facility.waste_categories ? 
                            (() => {
                              try {
                                return JSON.parse(facility.waste_categories).join(', ')
                              } catch {
                                return facility.waste_categories
                              }
                            })() 
                            : 'N/A'}
                        </td>
                        <td className="p-4 text-right text-text-secondary">
                          {facility.capacity_kg_per_day ? facility.capacity_kg_per_day.toLocaleString() : 'Unknown'}
                        </td>
                        <td className="p-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(facility.status)}`}>
                            {facility.status || 'Unknown'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  )
}