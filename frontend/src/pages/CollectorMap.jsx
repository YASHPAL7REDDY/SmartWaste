import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  Navbar, 
  LoadingState,
  EmptyState
} from '../components'

// Simple map implementation using Leaflet-like approach with canvas
// For production, you'd use leaflet or mapbox-gl

export function CollectorMap() {
  const { isAuthenticated, role } = useAuth()
  const [route, setRoute] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedAreas, setSelectedAreas] = useState([])
  const [vehicleCapacity, setVehicleCapacity] = useState(120)
  const canvasRef = useRef(null)
  
  if (!isAuthenticated || role !== 'collector') {
    return <Navigate to="/" replace />
  }

  const fetchRoute = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.post('/collector/routes/optimize', {
        collection_date: new Date().toISOString().split('T')[0]
      })
      setRoute(response.data)
      setSelectedAreas(response.data.route
        ?.filter(r => r.type === 'collection')
        .map(r => r.name) || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to optimize route')
    } finally {
      setLoading(false)
    }
  }

  const handleCapacityChange = (e) => {
    const val = parseFloat(e.target.value)
    if (!isNaN(val) && val > 0) {
      setVehicleCapacity(val)
    }
  }

  // Draw route on canvas
  useEffect(() => {
    if (!route || !canvasRef.current) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
    
    // Clear
    ctx.clearRect(0, 0, rect.width, rect.height)
    
    if (!route.route || route.route.length < 2) return
    
    // Find bounds
    const coords = route.route.map(p => [p.lon, p.lat])
    const minLon = Math.min(...coords.map(c => c[0]))
    const maxLon = Math.max(...coords.map(c => c[0]))
    const minLat = Math.min(...coords.map(c => c[1]))
    const maxLat = Math.max(...coords.map(c => c[1]))
    
    const padding = 0.01
    const lonRange = maxLon - minLon + padding * 2
    const latRange = maxLat - minLat + padding * 2
    
    const project = (lon, lat) => ({
      x: ((lon - (minLon - padding)) / lonRange) * rect.width,
      y: ((maxLat + padding - lat) / latRange) * rect.height
    })
    
    // Draw route lines
    ctx.strokeStyle = '#00d46a'
    ctx.lineWidth = 3
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.setLineDash([10, 5])
    
    ctx.beginPath()
    route.route.forEach((point, i) => {
      const p = project(point.lon, point.lat)
      if (i === 0) ctx.moveTo(p.x, p.y)
      else ctx.lineTo(p.x, p.y)
    })
    ctx.stroke()
    
    // Draw points
    route.route.forEach((point, i) => {
      const p = project(point.lon, point.lat)
      const isFirst = i === 0
      const isLast = i === route.route.length - 1
      const isDepot = point.type === 'depot'
      const isFacility = point.type === 'facility'
      const isCollection = point.type === 'collection'
      
      let color = '#00d46a'
      if (isDepot) color = '#888'
      else if (isFacility) color = '#3b82f6'
      else if (isCollection) {
        const risk = point.risk_level
        if (risk === 'critical') color = '#ef4444'
        else if (risk === 'high') color = '#f97316'
        else if (risk === 'medium') color = '#fbbf24'
        else color = '#00d46a'
      }
      
      ctx.beginPath()
      ctx.arc(p.x, p.y, isDepot ? 10 : isFacility ? 10 : 8, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()
      ctx.strokeStyle = '#0a0a0a'
      ctx.lineWidth = 3
      ctx.stroke()
      
      // Label
      ctx.fillStyle = '#fff'
      ctx.font = '12px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(point.name, p.x, p.y - 16)
      
      if (isCollection && point.predicted_waste_kg) {
        ctx.fillStyle = '#aaa'
        ctx.font = '10px system-ui'
        ctx.fillText(`${point.predicted_waste_kg} kg`, p.x, p.y + 20)
      }
    })
  }, [route])

  const riskColors = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-green-500/20 text-green-400 border-green-500/30'
  }

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Collection Route Map</h1>
          <p className="text-text-secondary mt-1">Optimized route based on overflow risk and vehicle capacity</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Panel */}
          <GlassCard className="lg:col-span-1">
            <h3 className="font-semibold text-text-primary mb-4">Route Optimization</h3>
            
            <GlassInput
              label="Vehicle Capacity (kg)"
              type="number"
              min="10"
              max="5000"
              value={vehicleCapacity}
              onChange={handleCapacityChange}
            />
            
            <div className="mb-4">
              <label className="glass-label">Selected Areas</label>
              <div className="flex flex-wrap gap-2">
                {selectedAreas.length > 0 ? (
                  selectedAreas.map(area => (
                    <span key={area} className="px-2 py-1 rounded-full text-xs font-medium bg-emerald/10 border border-emerald/30 text-emerald">
                      {area}
                    </span>
                  ))
                ) : (
                  <span className="text-text-muted text-sm">None selected</span>
                )}
              </div>
            </div>
            
            {route && (
              <div className="space-y-2 mb-4 p-4 bg-glass-white/50 rounded-glass-sm">
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Total Distance</span>
                  <span className="font-medium text-text-primary">{route.total_distance_km} km</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Total Waste</span>
                  <span className="font-medium text-text-primary">{route.total_waste_kg} kg</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Vehicle Capacity</span>
                  <span className="font-medium text-text-primary">{route.vehicle_capacity_kg} kg</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Utilization</span>
                  <span className="font-medium text-emerald">{route.utilization_pct}%</span>
                </div>
              </div>
            )}
            
            <GlassButton 
              variant="primary" 
              className="w-full" 
              onClick={fetchRoute}
              loading={loading}
            >
              {route ? 'RE-OPTIMIZE ROUTE' : 'OPTIMIZE ROUTE'}
            </GlassButton>
          </GlassCard>
          
          {/* Route Steps */}
          <GlassCard className="lg:col-span-2">
            <h3 className="font-semibold text-text-primary mb-4">Route Overview</h3>
            
            {route && route.route && route.route.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {route.route.map((point, i) => {
                  const isDepot = point.type === 'depot'
                  const isFacility = point.type === 'facility'
                  const isCollection = point.type === 'collection'
                  
                  let icon = '📍'
                  if (isDepot) icon = '🏭'
                  else if (isFacility) icon = '🏢'
                  else if (isCollection) icon = '🗑️'
                  
                  return (
                    <div 
                      key={`${point.name}-${i}`}
                      className={`flex items-center gap-4 p-3 rounded-glass-sm border transition-colors ${
                        isDepot ? 'border-blue-500/30 bg-blue-500/5' :
                        isFacility ? 'border-purple-500/30 bg-purple-500/5' :
                        'border-emerald/30 bg-emerald/5'
                      }`}
                    >
                      <div className="w-10 h-10 rounded-full flex items-center justify-center text-xl bg-glass-white/50">
                        {icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-text-primary">{point.name}</span>
                          {point.risk_level && (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${riskColors[point.risk_level?.toLowerCase()] || riskColors.low}`}>
                              {point.risk_level?.toUpperCase()}
                            </span>
                          )}
                          {isCollection && point.predicted_waste_kg && (
                            <span className="text-sm text-emerald font-medium">{point.predicted_waste_kg} kg</span>
                          )}
                        </div>
                        {point.distance_from_prev_km && (
                          <div className="text-xs text-text-secondary">
                            {point.distance_from_prev_km} km from previous
                          </div>
                        )}
                      </div>
                      <span className="text-lg font-bold text-text-secondary">{i === 0 ? 'START' : i === route.route.length - 1 ? 'END' : i}</span>
                    </div>
                  )
                })}
              </div>
            ) : (
              <EmptyState
                icon={
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                }
                title="No Route Generated"
                description="Set vehicle capacity and click Optimize Route to generate a collection route"
              />
            )}
          </GlassCard>
          
          {/* Map Canvas */}
          <GlassCard className="lg:col-span-3 h-[500px]">
            <h3 className="font-semibold text-text-primary mb-4">Route Visualization</h3>
            <div className="relative h-full bg-matte-black rounded-glass-sm overflow-hidden">
              <canvas 
                ref={canvasRef}
                className="w-full h-full"
                style={{ background: '#0a0a0a' }}
              />
              {!route && (
                <div className="absolute inset-0 flex items-center justify-center text-text-muted">
                  <p>Route will appear here after optimization</p>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}

import { Navigate } from 'react-router-dom'