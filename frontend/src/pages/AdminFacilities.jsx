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

export function AdminFacilities() {
  const { user } = useAuth()
  const [facilities, setFacilities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [types, setTypes] = useState([])

  useEffect(() => {
    fetchFacilities()
  }, [])

  const fetchFacilities = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get('/admin/facilities')
      setFacilities(response.data || [])
      const uniqueTypes = [...new Set(response.data.map(f => f.facility_type).filter(Boolean))]
      setTypes(uniqueTypes)
    } catch (err) {
      setError('Failed to load facilities')
    } finally {
      setLoading(false)
    }
  }

  const filteredFacilities = facilities.filter(f => {
    const matchesSearch = f.facility_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         f.area.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = !typeFilter || f.facility_type === typeFilter
    const matchesStatus = !statusFilter || f.status.toLowerCase() === statusFilter.toLowerCase()
    return matchesSearch && matchesType && matchesStatus
  })

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
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
            action={{ label: 'Retry', onClick: fetchFacilities }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Facilities Management</h1>
          <p className="text-text-secondary mt-1">Manage and monitor waste processing facilities</p>
        </div>

        {/* Filters */}
        <GlassCard className="mb-8">
          <h3 className="font-semibold text-text-primary mb-4">Filters</h3>
          <div className="flex flex-col sm:flex-row gap-4">
            <GlassInput
              label="Search"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or area"
              className="flex-1"
            />
            <GlassInput
              label="Facility Type"
              type="select"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              options={[{ value: '', label: 'All Types' }, ...types.map(t => ({ value: t, label: t }))]}
              className="sm:w-64"
            />
            <GlassInput
              label="Status"
              type="select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              options={[{ value: '', label: 'All Status' }, { value: 'active', label: 'Active' }, { value: 'inactive', label: 'Inactive' }]}
              className="sm:w-48"
            />
          </div>
        </GlassCard>

        {/* Facilities Table */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">All Facilities</h3>
            <span className="text-sm text-text-secondary">{filteredFacilities.length} of {facilities.length} facilities</span>
          </div>

          {filteredFacilities.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              }
              title="No Facilities Found"
              description="No facilities match the current filters"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Facility</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Type</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">City</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Categories</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Capacity (kg/day)</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Operator</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFacilities.map((facility) => (
                    <tr key={facility.facility_id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 font-medium text-text-primary">{facility.facility_name}</td>
                      <td className="p-4 text-text-secondary">{facility.facility_type}</td>
                      <td className="p-4 text-text-secondary">{facility.area || 'N/A'}</td>
                      <td className="p-4 text-text-secondary">{facility.city || 'N/A'}</td>
                      <td className="p-4 text-text-secondary text-sm">
                        {facility.waste_categories ? (
                          JSON.parse(facility.waste_categories).join(', ')
                        ) : 'N/A'}
                      </td>
                      <td className="p-4 text-right text-text-secondary">
                        {facility.capacity_kg_per_day ? facility.capacity_kg_per_day.toLocaleString() : 'Unknown'}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(facility.status)}`}>
                          {facility.status}
                        </span>
                      </td>
                      <td className="p-4 text-text-secondary">{facility.operator_name || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}