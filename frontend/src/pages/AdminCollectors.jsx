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

export function AdminCollectors() {
  const { user } = useAuth()
  const [collectors, setCollectors] = useState([])
  const [performance, setPerformance] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [days, setDays] = useState(30)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchCollectors()
    fetchPerformance()
  }, [days])

  const fetchCollectors = async () => {
    try {
      setError('')
      const response = await api.get('/admin/collectors')
      setCollectors(response.data || [])
    } catch (err) {
      console.error('Failed to load collectors')
    }
  }

  const fetchPerformance = async () => {
    try {
      const response = await api.get('/admin/collectors/performance', { params: { days } })
      setPerformance(response.data || [])
    } catch (err) {
      console.error('Failed to load collector performance')
    } finally {
      setLoading(false)
    }
  }

  const filteredCollectors = collectors.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.employee_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.vehicle_number?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'inactive': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    }
  }

  const getPerformance = (collectorId) => {
    return performance.find(p => p.collector_id === collectorId)
  }

  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading collectors..." />
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
            title="Unable to Load Collectors"
            description={error}
            action={{ label: 'Retry', onClick: fetchCollectors }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-text-primary">Collector Management</h1>
            <p className="text-text-secondary mt-1">Monitor and manage waste collection personnel</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-text-secondary">Performance Period:</span>
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="px-3 py-2 bg-glass-white/10 border border-glass-border rounded-glass-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-emerald/50"
            >
              <option value={7}>7 Days</option>
              <option value={30}>30 Days</option>
              <option value={90}>90 Days</option>
            </select>
          </div>
        </div>

        {/* Search */}
        <GlassCard className="mb-8">
          <div className="flex gap-4">
            <GlassInput
              label="Search Collectors"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, employee ID, or vehicle number"
              className="flex-1 max-w-md"
            />
          </div>
        </GlassCard>

        {/* Collectors Table */}
        <GlassCard className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">All Collectors</h3>
            <span className="text-sm text-text-secondary">{filteredCollectors.length} of {collectors.length} collectors</span>
          </div>

          {filteredCollectors.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              }
              title="No Collectors Found"
              description="No collectors match the current search"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Collector</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Employee ID</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Vehicle</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Capacity (kg)</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Assigned Areas</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCollectors.map((collector) => (
                    <tr key={collector.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 font-medium text-text-primary">{collector.name}</td>
                      <td className="p-4 text-text-secondary font-mono">{collector.employee_id || 'N/A'}</td>
                      <td className="p-4 text-text-secondary">{collector.vehicle_number || 'Not assigned'}</td>
                      <td className="p-4 text-text-secondary">{collector.vehicle_capacity_kg || 'Not set'}</td>
                      <td className="p-4 text-text-secondary text-sm max-w-xs truncate">
                        {collector.assigned_areas ? collector.assigned_areas : 'None'}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(collector.is_active ? 'active' : 'inactive')}`}>
                          {collector.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>

        {/* Performance Table */}
        {performance.length > 0 && (
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-text-primary">Collector Performance ({days} days)</h3>
              <span className="text-sm text-text-secondary">{performance.length} collectors with activity</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Collector</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total Collections</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Completed</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Completion Rate</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Predicted (kg)</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Collected (kg)</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  {performance.map((perf) => {
                    const collector = collectors.find(c => c.id === perf.collector_id)
                    const completionRate = perf.total_collections > 0 
                      ? ((perf.completed / perf.total_collections) * 100).toFixed(1)
                      : 0
                    const accuracy = perf.total_predicted > 0
                      ? (100 - Math.abs(perf.total_predicted - perf.total_collected) / perf.total_predicted * 100).toFixed(1)
                      : 0
                    return (
                      <tr key={perf.collector_id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                        <td className="p-4 font-medium text-text-primary">
                          {collector?.name || perf.collector_id.slice(0, 16) + '...'}
                        </td>
                        <td className="p-4 text-right text-text-primary">{perf.total_collections}</td>
                        <td className="p-4 text-right text-text-primary">{perf.completed}</td>
                        <td className="p-4 text-right font-medium text-emerald">{completionRate}%</td>
                        <td className="p-4 text-right text-text-secondary">{perf.total_predicted?.toFixed(1)}</td>
                        <td className="p-4 text-right text-text-secondary">{perf.total_collected?.toFixed(1)}</td>
                        <td className="p-4 text-right font-medium text-emerald">{accuracy}%</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  )
}