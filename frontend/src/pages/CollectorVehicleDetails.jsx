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

export function CollectorVehicleDetails() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [vehicleInfo, setVehicleInfo] = useState(null)
  const [collector, setCollector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [capacityLoading, setCapacityLoading] = useState(false)
  const [capacityError, setCapacityError] = useState('')
  const [capacitySuccess, setCapacitySuccess] = useState('')
  const [capacityInput, setCapacityInput] = useState('')

  useEffect(() => {
    fetchVehicleDetails()
  }, [])

  const fetchVehicleDetails = async () => {
    try {
      setLoading(true)
      const [dashboardRes, vehicleRes] = await Promise.all([
        api.get('/collector/dashboard'),
        api.get('/collector/vehicle-info')
      ])
      setCollector(dashboardRes.data.collector)
      setVehicleInfo(vehicleRes.data)
      if (vehicleRes.data?.capacity_kg) {
        setCapacityInput(vehicleRes.data.capacity_kg.toString())
      }
    } catch (err) {
      setError('Failed to load vehicle details')
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
      fetchVehicleDetails()
    } catch (err) {
      setCapacityError(err.response?.data?.detail || 'Failed to save vehicle capacity')
    } finally {
      setCapacityLoading(false)
    }
  }

  const getUtilizationColor = (pct) => {
    if (pct >= 100) return 'text-red-400'
    if (pct >= 90) return 'text-yellow-400'
    return 'text-emerald'
  }

  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading vehicle details..." />
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
            title="Unable to Load Vehicle Details"
            description={error}
            action={{ label: 'Retry', onClick: fetchVehicleDetails }}
          />
        </div>
      </div>
    )
  }

  const collectorName = collector?.name || 'Not available'
  const collectorEmail = user?.email || 'Not available'
  const vehicleNumber = collector?.vehicle_number || 'Not available'
  const capacity = vehicleInfo?.capacity_kg ?? 0
  const plannedLoad = vehicleInfo?.planned_load_kg ?? 0
  const remaining = vehicleInfo?.remaining_kg ?? 0
  const utilization = vehicleInfo?.utilization_pct ?? 0
  const overCapacity = vehicleInfo?.over_capacity ?? false
  const warning = vehicleInfo?.warning ?? false

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Vehicle Details</h1>
          <p className="text-text-secondary mt-1">Collector vehicle information and capacity management</p>
        </div>

        {/* Collector Info */}
        <GlassCard className="mb-8">
          <h3 className="font-semibold text-text-primary mb-4">Collector Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="glass-label">Name</label>
              <p className="text-text-primary font-medium">{collectorName}</p>
            </div>
            <div>
              <label className="glass-label">Email</label>
              <p className="text-text-primary font-medium">{collectorEmail}</p>
            </div>
            <div>
              <label className="glass-label">Vehicle Number</label>
              <p className="text-text-primary font-medium">{vehicleNumber}</p>
            </div>
            <div>
              <label className="glass-label">Status</label>
              <p className="text-text-primary font-medium">
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                  Active
                </span>
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Vehicle Capacity Section */}
        <GlassCard className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">Vehicle Capacity</h3>
          </div>
          
          {/* Capacity Display */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
              <label className="glass-label">Capacity</label>
              <p className="text-2xl font-bold text-text-primary">{capacity} kg</p>
            </div>
            <div className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
              <label className="glass-label">Planned Load</label>
              <p className="text-2xl font-bold text-text-primary">{plannedLoad.toFixed(1)} kg</p>
            </div>
            <div className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
              <label className="glass-label">Remaining</label>
              <p className="text-2xl font-bold {getUtilizationColor(utilization)}">{remaining.toFixed(1)} kg</p>
            </div>
            <div className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
              <label className="glass-label">Utilization</label>
              <p className="text-2xl font-bold {getUtilizationColor(utilization)}">{utilization.toFixed(1)}%</p>
            </div>
          </div>

          {/* Utilization Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text-secondary">Utilization</span>
              <span className={`font-medium ${getUtilizationColor(utilization)}`}>
                {utilization.toFixed(1)}%
              </span>
            </div>
            <div className="h-3 bg-glass-white rounded-full overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-300"
                style={{ 
                  width: `${Math.min(utilization, 100)}%`,
                  background: overCapacity ? 'linear-gradient(90deg, #ef4444, #f87171)' : 
                              warning ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' :
                              'linear-gradient(90deg, #00d46a, #34e885)'
                }}
              />
            </div>
          </div>

          {overCapacity && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm text-red-400 text-sm mb-4">
              ⚠️ OVER CAPACITY - Vehicle is overloaded
            </div>
          )}
          {warning && !overCapacity && (
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm text-yellow-400 text-sm mb-4">
              ⚠️ High utilization - Near capacity
            </div>
          )}

          {/* Edit Capacity */}
          <div className="border-t border-glass-border pt-6">
            <h4 className="font-medium text-text-primary mb-4">Edit Capacity</h4>
            <div className="flex flex-col sm:flex-row gap-3">
              <GlassInput
                label="Vehicle Capacity (kg)"
                type="number"
                min="1"
                step="1"
                value={capacityInput}
                onChange={(e) => setCapacityInput(e.target.value)}
                placeholder="Enter new vehicle capacity in kg"
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
          </div>
        </GlassCard>

        {/* Back Button */}
        <div className="flex gap-4">
          <GlassButton variant="default" onClick={() => navigate('/collector')}>
            ← Back to Dashboard
          </GlassButton>
        </div>
      </div>
    </div>
  )
}