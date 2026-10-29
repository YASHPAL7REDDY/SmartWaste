import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  GlassInput,
  Navbar, 
  LoadingState, 
  EmptyState,
  Modal
} from '../components'

export function CollectorCollections() {
  const { user } = useAuth()
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [vehicleCapacity, setVehicleCapacity] = useState(150)
  const [dateFilter, setDateFilter] = useState('')
  
  // Record Actual Collection Modal State
  const [recordModalOpen, setRecordModalOpen] = useState(false)
  const [recordCollection, setRecordCollection] = useState(null)
  const [recordLoading, setRecordLoading] = useState(false)
  const [recordError, setRecordError] = useState('')
  const [recordForm, setRecordForm] = useState({
    wet_kg: '',
    dry_kg: '',
    plastic_kg: '',
    glass_kg: '',
    metal_kg: '',
    medical_kg: '',
    vehicle_capacity_kg: ''
  })
  const [recordValidationErrors, setRecordValidationErrors] = useState({})
  
  const toggleSelection = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }
  
  const getSelectedCollections = () => {
    return collections.filter(c => selectedIds.has(c.id))
  }
  
  const getTotalSelectedWeight = () => {
    return getSelectedCollections().reduce((sum, c) => sum + (c.predicted_waste_kg || 0), 0)
  }
  
  const getRemainingCapacity = () => {
    return vehicleCapacity - getTotalSelectedWeight()
  }
  
  const isOverCapacity = () => {
    return getTotalSelectedWeight() > vehicleCapacity
  }

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical':
      case 'high': return 'text-red-400'
      case 'medium': return 'text-yellow-400'
      default: return 'text-green-400'
    }
  }
  
  const getRiskBgColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'bg-red-500/20 border-red-500/30'
      case 'high': return 'bg-orange-500/20 border-orange-500/30'
      case 'medium': return 'bg-yellow-500/20 border-yellow-500/30'
      default: return 'bg-green-500/20 border-green-500/30'
    }
  }
  
  const parseWasteBreakdown = (breakdown) => {
    if (!breakdown) return {}
    try {
      return JSON.parse(breakdown)
    } catch {
      return {}
    }
  }
  
  const formatBreakdown = (breakdown) => {
    const parsed = parseWasteBreakdown(breakdown)
    const wasteTypes = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical']
    return wasteTypes
      .filter(wt => parsed[wt] && parsed[wt] > 0)
      .map(wt => `${wt.charAt(0).toUpperCase() + wt.slice(1)}: ${parsed[wt]}kg`)
      .join(' • ')
  }
  
  const getPredictedBreakdown = (collection) => {
    return parseWasteBreakdown(collection.waste_breakdown_predicted)
  }
  
  const getTotalPredicted = (collection) => {
    const breakdown = getPredictedBreakdown(collection)
    return Object.values(breakdown).reduce((sum, v) => sum + (v || 0), 0)
  }
  
  const getTotalActual = () => {
    return Object.values(recordForm).reduce((sum, v) => sum + (parseFloat(v) || 0), 0)
  }
  
  const validateRecordForm = () => {
    const errors = {}
    const wasteTypes = ['wet_kg', 'dry_kg', 'plastic_kg', 'glass_kg', 'metal_kg', 'medical_kg']
    let hasValues = false
    
    wasteTypes.forEach(wt => {
      const value = parseFloat(recordForm[wt]) || 0
      if (value < 0) {
        errors[wt] = 'Quantity cannot be negative'
      }
      if (value > 0) hasValues = true
    })
    
    const vehicleCap = parseFloat(recordForm.vehicle_capacity_kg) || vehicleCapacity
    const totalActual = getTotalActual()
    
    if (!hasValues) {
      errors.general = 'At least one waste type quantity must be greater than 0'
    }
    
    if (totalActual > vehicleCap) {
      errors.capacity = `Total collected (${totalActual.toFixed(1)} kg) exceeds vehicle capacity (${vehicleCap.toFixed(1)} kg)`
    }
    
    if (!recordCollection) {
      errors.general = 'No collection selected'
    }
    
    setRecordValidationErrors(errors)
    return Object.keys(errors).length === 0
  }
  
  const handleRecordSubmit = async () => {
    if (!validateRecordForm()) return
    
    setRecordLoading(true)
    setRecordError('')
    
    try {
      const payload = {
        area_collection_id: recordCollection.id,
        wet_kg: parseFloat(recordForm.wet_kg) || 0,
        dry_kg: parseFloat(recordForm.dry_kg) || 0,
        plastic_kg: parseFloat(recordForm.plastic_kg) || 0,
        glass_kg: parseFloat(recordForm.glass_kg) || 0,
        metal_kg: parseFloat(recordForm.metal_kg) || 0,
        medical_kg: parseFloat(recordForm.medical_kg) || 0,
        vehicle_capacity_kg: parseFloat(recordForm.vehicle_capacity_kg) || vehicleCapacity
      }
      
      const response = await api.post(`/collector/collection/${recordCollection.id}/actual`, payload)
      
      // Refresh collections list
      await fetchCollections()
      
      // Close modal and reset
      setRecordModalOpen(false)
      setRecordCollection(null)
      setRecordForm({
        wet_kg: '', dry_kg: '', plastic_kg: '', glass_kg: '', metal_kg: '', medical_kg: '', vehicle_capacity_kg: ''
      })
      setRecordValidationErrors({})
      
      // Show success
      alert(`Collection recorded successfully! Total: ${response.data.total_collected_kg} kg`)
    } catch (err) {
      setRecordError(err.response?.data?.detail || 'Failed to record actual collection')
      console.error(err)
    } finally {
      setRecordLoading(false)
    }
  }
  
  const openRecordModal = (collection) => {
    const predictedBreakdown = getPredictedBreakdown(collection)
    setRecordCollection(collection)
    setRecordForm({
      wet_kg: predictedBreakdown.wet?.toString() || '',
      dry_kg: predictedBreakdown.dry?.toString() || '',
      plastic_kg: predictedBreakdown.plastic?.toString() || '',
      glass_kg: predictedBreakdown.glass?.toString() || '',
      metal_kg: predictedBreakdown.metal?.toString() || '',
      medical_kg: predictedBreakdown.medical?.toString() || '',
      vehicle_capacity_kg: vehicleCapacity.toString()
    })
    setRecordValidationErrors({})
    setRecordError('')
    setRecordModalOpen(true)
  }
  
  const closeRecordModal = () => {
    setRecordModalOpen(false)
    setRecordCollection(null)
    setRecordForm({
      wet_kg: '', dry_kg: '', plastic_kg: '', glass_kg: '', metal_kg: '', medical_kg: '', vehicle_capacity_kg: ''
    })
    setRecordValidationErrors({})
    setRecordError('')
  }

  useEffect(() => {
    fetchCollections()
    fetchVehicleInfo()
  }, [dateFilter])
  
  const fetchCollections = async () => {
    try {
      setLoading(true)
      const params = {}
      if (dateFilter) params.collection_date = dateFilter
      const response = await api.get('/collector/collections', { params })
      setCollections(response.data)
    } catch (err) {
      setError('Failed to load collections')
    } finally {
      setLoading(false)
    }
  }
  
  const fetchVehicleInfo = async () => {
    try {
      const response = await api.get('/collector/me')
      setVehicleCapacity(response.data?.vehicle_capacity_kg || 150)
    } catch (err) {
      console.error('Failed to load vehicle info')
    }
  }
  
  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading collections..." />
        </div>
      </div>
    )
  }
  
  const wasteTypes = [
    { key: 'wet_kg', label: 'Wet Waste', color: 'bg-green-500' },
    { key: 'dry_kg', label: 'Dry Waste', color: 'bg-gray-500' },
    { key: 'plastic_kg', label: 'Plastic', color: 'bg-blue-500' },
    { key: 'glass_kg', label: 'Glass', color: 'bg-cyan-500' },
    { key: 'metal_kg', label: 'Metal', color: 'bg-amber-500' },
    { key: 'medical_kg', label: 'Medical', color: 'bg-red-500' }
  ]
  
  const totalPredicted = recordCollection ? getTotalPredicted(recordCollection) : 0
  const totalActual = getTotalActual()
  const vehicleCap = parseFloat(recordForm.vehicle_capacity_kg) || vehicleCapacity
  const remainingCapacity = vehicleCap - totalActual
  const difference = totalActual - totalPredicted

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Collections</h1>
          <p className="text-text-secondary mt-1">Select collections for your route</p>
        </div>
        
        {/* Date Filter */}
        <GlassCard className="mb-6">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <GlassInput
              label="Filter by Date (optional)"
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="sm:w-64"
            />
            <GlassButton variant="ghost" onClick={() => setDateFilter('')}>
              Clear Filter
            </GlassButton>
          </div>
        </GlassCard>
        
        {/* Vehicle Capacity & Selection Summary */}
        <GlassCard className="mb-8">
          <h3 className="font-semibold text-text-primary mb-4">Route Planning</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <GlassInput
              label="Vehicle Capacity (kg)"
              type="number"
              min="1"
              step="1"
              value={vehicleCapacity}
              onChange={(e) => setVehicleCapacity(parseFloat(e.target.value) || 0)}
              className="w-full"
            />
            <div className="flex flex-col justify-between">
              <span className="text-text-secondary text-sm">Total Selected</span>
              <span className="text-2xl font-bold text-text-primary">
                {getTotalSelectedWeight().toFixed(1)} / {vehicleCapacity} kg
              </span>
            </div>
            <div className="flex flex-col justify-between">
              <span className="text-text-secondary text-sm">Remaining Capacity</span>
              <span className={`text-2xl font-bold ${getRemainingCapacity() < 0 ? 'text-red-400' : 'text-emerald'}`}>
                {getRemainingCapacity().toFixed(1)} kg
              </span>
            </div>
          </div>
          
          {isOverCapacity() && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm text-red-400 text-sm mb-4">
              ⚠️ OVER CAPACITY - Remove some collections or increase vehicle capacity
            </div>
          )}
        </GlassCard>
        
        {/* Collections List */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">Available Collections</h3>
            <span className="text-sm text-text-secondary">{collections.length} collections</span>
          </div>
          
          {collections.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              }
              title="No Collections Found"
              description={dateFilter ? "No collections found for this date" : "No collections available"}
            />
          ) : (
            <div className="space-y-3">
              {collections.map((collection) => {
                const isSelected = selectedIds.has(collection.id)
                const riskLevel = collection.risk_level?.toLowerCase() || 'low'
                const breakdown = parseWasteBreakdown(collection.waste_breakdown_predicted)
                const isCompleted = collection.status === 'completed'
                
                return (
                  <div 
                    key={collection.id}
                    onClick={() => !isCompleted && toggleSelection(collection.id)}
                    className={`p-4 rounded-glass-sm border transition-all duration-fast ${isCompleted ? 'cursor-default opacity-70' : 'cursor-pointer'} ${
                      isSelected ? 'border-emerald/50 bg-emerald/5 ring-2 ring-emerald/20' : 'border-glass-border bg-glass-white/50'
                    } ${getRiskBgColor(riskLevel)}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => { e.stopPropagation(); if (!isCompleted) toggleSelection(collection.id); }}
                          disabled={isCompleted}
                          className="w-5 h-5 text-emerald border-glass-border rounded focus:ring-2 focus:ring-emerald/50 mt-0.5 flex-shrink-0"
                        />
                        <div className="min-w-0">
                          <div className="flex items-center gap-3 flex-wrap mb-2">
                            <h4 className="font-semibold text-text-primary truncate">{collection.area}</h4>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskBgColor(riskLevel)} text-${getRiskColor(riskLevel)}`}>
                              {collection.risk_level?.toUpperCase() || 'NORMAL'}
                            </span>
                            {collection.route_sequence && (
                              <span className="px-2 py-1 bg-emerald/10 text-emerald rounded-full text-xs font-medium">
                                Seq: {collection.route_sequence}
                              </span>
                            )}
                            {isCompleted && (
                              <span className="px-2 py-1 bg-emerald/20 text-emerald rounded-full text-xs font-medium">
                                ✓ Completed
                              </span>
                            )}
                          </div>
                          
                          <div className="flex flex-wrap gap-4 text-sm text-text-secondary mb-2">
                            <span>Predicted: <span className="font-medium text-text-primary">{collection.predicted_waste_kg?.toFixed(1) || 0} kg</span></span>
                            <span>Collected: <span className="font-medium text-text-primary">{collection.collected_waste_kg?.toFixed(1) || 0} kg</span></span>
                            <span>Status: <span className="font-medium text-text-primary capitalize">{collection.status?.replace('_', ' ')}</span></span>
                          </div>
                          
                          {/* Waste Breakdown - Always Visible */}
                          <div className="flex flex-wrap gap-2 text-xs">
                            {['wet', 'dry', 'plastic', 'glass', 'metal', 'medical'].map(wt => 
                              breakdown[wt] && breakdown[wt] > 0 && (
                                <span key={wt} className="px-2 py-0.5 bg-emerald/10 text-emerald rounded-full text-xs font-medium">
                                  {wt.charAt(0).toUpperCase() + wt.slice(1)}: {breakdown[wt]}kg
                                </span>
                              )
                            )}
                            {Object.keys(breakdown).length === 0 && (
                              <span className="text-text-muted text-xs">No waste breakdown available</span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end gap-2 flex-shrink-0">
                        <span className="font-medium text-text-primary">
                          {collection.predicted_waste_kg?.toFixed(1) || 0} kg
                        </span>
                        {collection.planned_load_kg && (
                          <span className="text-xs text-text-secondary">Planned: {collection.planned_load_kg.toFixed(1)} kg</span>
                        )}
                        {!isCompleted && (
                          <GlassButton 
                            variant="primary" 
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); openRecordModal(collection); }}
                          >
                            Record Actual
                          </GlassButton>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </GlassCard>
        
        {/* Record Actual Collection Modal */}
        <Modal
          isOpen={recordModalOpen}
          onClose={closeRecordModal}
          title="Record Actual Collection"
          size="lg"
        >
          {recordCollection && (
            <div className="space-y-4">
              <div className="text-sm text-text-secondary mb-2">
                Area: <span className="font-medium text-text-primary">{recordCollection.area}</span> • 
                Date: <span className="font-medium text-text-primary">{recordCollection.collection_date}</span>
              </div>
              
              {recordError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm text-red-400 text-sm">
                  {recordError}
                </div>
              )}
              
              {recordValidationErrors.general && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm text-red-400 text-sm">
                  {recordValidationErrors.general}
                </div>
              )}
              
              {recordValidationErrors.capacity && (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm text-yellow-400 text-sm">
                  ⚠️ {recordValidationErrors.capacity}
                </div>
              )}
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {wasteTypes.map(wt => {
                  const predicted = getPredictedBreakdown(recordCollection)[wt.key.replace('_kg', '')] || 0
                  const actual = parseFloat(recordForm[wt.key]) || 0
                  const error = actual - predicted
                  const errorColor = error > 0 ? 'text-red-400' : error < 0 ? 'text-blue-400' : 'text-emerald-400'
                  
                  return (
                    <div key={wt.key} className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`w-3 h-3 rounded-full ${wt.color}`}></span>
                        <label className="font-medium text-text-primary">{wt.label}</label>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                        <div>
                          <span className="text-text-secondary">Predicted:</span>
                          <span className="font-medium text-text-primary ml-1">{predicted.toFixed(1)} kg</span>
                        </div>
                        <div>
                          <span className="text-text-secondary">Actual:</span>
                          <span className="font-medium text-text-primary ml-1">{actual.toFixed(1)} kg</span>
                        </div>
                      </div>
                      <GlassInput
                        label={`${wt.label} (kg)`}
                        type="number"
                        min="0"
                        step="0.1"
                        value={recordForm[wt.key]}
                        onChange={(e) => setRecordForm(prev => ({ ...prev, [wt.key]: e.target.value }))}
                        error={recordValidationErrors[wt.key]}
                        className="w-full"
                      />
                      {error !== 0 && (
                        <div className={`text-xs mt-1 ${errorColor}`}>
                          Difference: {error > 0 ? '+' : ''}{error.toFixed(1)} kg
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
              
              {/* Summary */}
              <div className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-text-secondary text-xs">Predicted Total</div>
                    <div className="text-xl font-bold text-text-primary">{totalPredicted.toFixed(1)} kg</div>
                  </div>
                  <div>
                    <div className="text-text-secondary text-xs">Actual Total</div>
                    <div className="text-xl font-bold text-text-primary">{totalActual.toFixed(1)} kg</div>
                  </div>
                  <div>
                    <div className="text-text-secondary text-xs">Difference</div>
                    <div className={`text-xl font-bold ${difference > 0 ? 'text-red-400' : difference < 0 ? 'text-blue-400' : 'text-emerald-400'}`}>
                      {difference > 0 ? '+' : ''}{difference.toFixed(1)} kg
                    </div>
                  </div>
                  <div>
                    <div className="text-text-secondary text-xs">Vehicle Capacity</div>
                    <div className="text-xl font-bold text-text-primary">{vehicleCap.toFixed(1)} kg</div>
                  </div>
                  <div className="md:col-span-2">
                    <div className="text-text-secondary text-xs">Remaining Capacity</div>
                    <div className={`text-xl font-bold ${remainingCapacity < 0 ? 'text-red-400' : 'text-emerald'}`}>
                      {remainingCapacity.toFixed(1)} kg
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 pt-4 border-t border-glass-border">
                <GlassButton variant="ghost" onClick={closeRecordModal} disabled={recordLoading}>
                  Cancel
                </GlassButton>
                <GlassButton 
                  variant="primary" 
                  onClick={handleRecordSubmit} 
                  disabled={recordLoading}
                  loading={recordLoading}
                >
                  Confirm Collection
                </GlassButton>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </div>
  )
}