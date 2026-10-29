import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { 
  GlassCard, 
  GlassButton, 
  GlassInput,
  Navbar, 
  LoadingState, 
  EmptyState 
} from '../components'
import { format } from 'date-fns'

export function CollectorDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [capacityLoading, setCapacityLoading] = useState(false)
  const [capacityError, setCapacityError] = useState('')
  const [capacitySuccess, setCapacitySuccess] = useState('')
  const [capacityInput, setCapacityInput] = useState('')
  
  useEffect(() => {
    fetchDashboard()
  }, [])
  
  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.get('/collector/dashboard')
      setDashboard(response.data)
      // Pre-fill capacity input with existing vehicle capacity
      if (response.data?.collector?.vehicle_capacity_kg) {
        setCapacityInput(response.data.collector.vehicle_capacity_kg.toString())
      }
    } catch (err) {
      setError('Failed to load collector dashboard')
    } finally {
      setLoading(false)
    }
  }
  
  const handleCapacitySave = async () => {
    const capacity = parseFloat(capacityInput)
    if (isNaN(capacity) || capacity <= 0) {
      setCapacityError('Please enter a valid capacity greater than 0')
      return
    }
    
    setCapacityLoading(true)
    setCapacityError('')
    setCapacitySuccess('')
    
    try {
      await api.patch('/collector/vehicle-capacity', { capacity_kg: capacity })
      setCapacitySuccess('Vehicle capacity updated successfully.')
      // Refresh dashboard to show updated capacity
      fetchDashboard()
    } catch (err) {
      setCapacityError(err.response?.data?.detail || 'Failed to save vehicle capacity')
    } finally {
      setCapacityLoading(false)
    }
  }
  
  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      default: return 'bg-green-500/20 text-green-400 border-green-500/30'
    }
  }
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-500/20 text-green-400'
      case 'in_progress': return 'bg-blue-500/20 text-blue-400'
      case 'assigned': return 'bg-yellow-500/20 text-yellow-400'
      default: return 'bg-gray-500/20 text-gray-400'
    }
  }
  
  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading collector dashboard..." />
        </div>
      </div>
    )
  }
  
  if (!dashboard) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <EmptyState
            title="Unable to Load Dashboard"
            description={error}
            action={{ label: 'Retry', onClick: fetchDashboard }}
          />
        </div>
      </div>
    )
  }
  
  const { collector, today_collections, overflow_risks } = dashboard
const vehicle_info = {
  capacity_kg: collector?.vehicle_capacity_kg || 0,
  planned_load_kg: today_collections?.reduce((sum, c) => sum + (c.planned_load_kg || c.predicted_waste_kg || 0), 0) || 0,
  remaining_kg: Math.max(0, (collector?.vehicle_capacity_kg || 0) - (today_collections?.reduce((sum, c) => sum + (c.planned_load_kg || c.predicted_waste_kg || 0), 0) || 0)),
  utilization_pct: collector?.vehicle_capacity_kg ? ((today_collections?.reduce((sum, c) => sum + (c.planned_load_kg || c.predicted_waste_kg || 0), 0) || 0) / collector.vehicle_capacity_kg) * 100 : 0,
  over_capacity: collector?.vehicle_capacity_kg ? (today_collections?.reduce((sum, c) => sum + (c.planned_load_kg || c.predicted_waste_kg || 0), 0) || 0) > collector.vehicle_capacity_kg : false,
  warning: collector?.vehicle_capacity_kg ? ((today_collections?.reduce((sum, c) => sum + (c.planned_load_kg || c.predicted_waste_kg || 0), 0) || 0) / collector.vehicle_capacity_kg) * 100 >= 90 : false,
}
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Collector Dashboard</h1>
          <p className="text-text-secondary mt-1">{collector?.name} • Vehicle: {collector?.vehicle_number || 'Not assigned'}</p>
        </div>
        
        {/* Vehicle Capacity Input */}
        <GlassCard className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">Vehicle Capacity</h3>
            <span className="text-sm text-text-muted">Current: {vehicle_info.capacity_kg} kg</span>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <GlassInput
              label="Vehicle Capacity (kg)"
              type="number"
              min="1"
              step="1"
              value={capacityInput}
              onChange={(e) => setCapacityInput(e.target.value)}
              placeholder="Enter vehicle capacity in kg"
              error={capacityError}
              className="flex-1"
            />
            <GlassButton 
              variant="primary" 
              onClick={handleCapacitySave} 
              loading={capacityLoading}
              className="whitespace-nowrap"
            >
              SAVE CAPACITY
            </GlassButton>
          </div>
          <div className="mt-2 text-sm text-text-secondary">
            Current capacity: <span className="font-medium text-text-primary">{vehicle_info.capacity_kg} kg</span>
          </div>
          {capacityError && (
            <div className="inline-error mt-3" role="alert">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{capacityError}</span>
            </div>
          )}
          {capacitySuccess && (
            <div className="inline-error mt-3 bg-green-500/10 border-green-500/20 text-green-400" role="alert">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>{capacitySuccess}</span>
            </div>
          )}
        </GlassCard>
        
        {/* Collector Info & Vehicle */}
        <div className="card-grid mb-8">
          <GlassCard className="md:col-span-2">
            <h3 className="font-semibold text-text-primary mb-4">Today's Collections</h3>
            {today_collections?.length > 0 ? (
              <div className="space-y-3">
                {today_collections.map((collection, i) => (
                  <div key={collection.id} className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-text-primary">{collection.area}</h4>
                        <p className="text-sm text-text-secondary">Sequence: {collection.route_sequence}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(collection.status)}`}>
                        {collection.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Predicted</span>
                        <span className="font-medium text-text-primary">{collection.predicted_waste_kg?.toFixed(1) || 0} kg</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Collected</span>
                        <span className="font-medium text-text-primary">{collection.collected_waste_kg?.toFixed(1) || 0} kg</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Priority</span>
                        <span className="font-medium text-text-primary">{collection.priority || 'Normal'}</span>
                      </div>
                    </div>
                    {collection.waste_breakdown_predicted && (
                      <details className="mt-2">
                        <summary className="text-sm text-text-secondary cursor-pointer">Waste Breakdown</summary>
                        <pre className="text-xs text-text-muted mt-1 p-2 bg-matte-black rounded overflow-x-auto">
                          {collection.waste_breakdown_predicted}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                }
                title="No Collections Today"
                description="No areas assigned for collection today"
              />
            )}
          </GlassCard>
          
          <GlassCard>
            <h3 className="font-semibold text-text-primary mb-4">Vehicle Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-text-secondary">Capacity</span>
                <span className="font-medium text-text-primary">{vehicle_info.capacity_kg} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Planned Load</span>
                <span className="font-medium text-text-primary">{vehicle_info.planned_load_kg.toFixed(1)} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Remaining</span>
                <span className="font-medium text-text-primary">{vehicle_info.remaining_kg.toFixed(1)} kg</span>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-text-secondary">Utilization</span>
                  <span className={vehicle_info.utilization_pct >= 90 ? 'font-medium text-red-400' : 'font-medium text-text-primary'}>
                    {vehicle_info.utilization_pct.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-glass-white rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-300"
                    style={{ 
                      width: `${Math.min(vehicle_info.utilization_pct, 100)}%`,
                      background: vehicle_info.over_capacity ? 'linear-gradient(90deg, #ef4444, #f87171)' : 
                                  vehicle_info.warning ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' :
                                  'linear-gradient(90deg, #00d46a, #34e885)'
                    }}
                  />
                </div>
              </div>
              {vehicle_info.over_capacity && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm text-red-400 text-sm">
                  ⚠️ OVER CAPACITY - Consider splitting collections
                </div>
              )}
              {vehicle_info.warning && !vehicle_info.over_capacity && (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm text-yellow-400 text-sm">
                  ⚠️ High utilization - Near capacity
                </div>
              )}
            </div>
          </GlassCard>
        </div>
        
        {/* Overflow Risks */}
        {(overflow_risks || []).length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Overflow Risk Alerts</h2>
            <div className="card-grid">
              {overflow_risks.map((risk) => (
                <GlassCard key={risk.id} className={`border-l-4 ${getRiskColor(risk.risk_level)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-text-primary">{risk.area}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskColor(risk.risk_level)}`}>
                      {risk.risk_level?.toUpperCase()}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Predicted</span>
                      <span className="font-medium text-text-primary">{risk.predicted_total_waste_kg?.toFixed(1) || 'N/A'} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Capacity</span>
                      <span className="font-medium text-text-primary">{risk.capacity_proxy_kg?.toFixed(1) || 'N/A'} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Utilization</span>
                      <span className="font-medium text-text-primary">
                        {risk.capacity_utilization ? (risk.capacity_utilization * 100).toFixed(1) + '%' : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Risk Score</span>
                      <span className="font-medium text-text-primary">{risk.risk_score?.toFixed(2) || 'N/A'}</span>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>
        )}
        
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-4">
          <GlassButton variant="primary" onClick={() => navigate('/collector/collections')}>
            View All Collections
          </GlassButton>
          <GlassButton variant="default" onClick={() => navigate('/collector/vehicle')}>
            Vehicle Details
          </GlassButton>
          <GlassButton variant="default" onClick={() => navigate('/collector/facilities')}>
            Facilities
          </GlassButton>
        </div>
      </div>
    </div>
  )
}