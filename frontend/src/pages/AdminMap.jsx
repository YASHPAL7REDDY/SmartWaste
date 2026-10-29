import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  GlassInput, 
  Navbar, 
  LoadingState,
  EmptyState
} from '../components'

export function AdminMap() {
  const { isAuthenticated, role } = useAuth()
  const [facilities, setFacilities] = useState([])
  const [highWasteAreas, setHighWasteAreas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filterType, setFilterType] = useState('all')
  const canvasRef = useRef(null)
  
  if (!isAuthenticated || role !== 'admin') {
    return <Navigate to="/" replace />
  }

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [facilitiesRes, highWasteRes] = await Promise.all([
        api.get('/facilities', { params: { limit: 500 } }),
        api.get('/admin/high-waste-areas', { params: { limit: 50 } })
      ])
      setFacilities(facilitiesRes.data || [])
      setHighWasteAreas(highWasteRes.data || [])
    } catch (err) {
      setError('Failed to load map data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Draw map on canvas
  useEffect(() => {
    if (!canvasRef.current) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
    
    ctx.clearRect(0, 0, rect.width, rect.height)
    
    // Combine all points
    const allPoints = [
      ...facilities.filter(f => f.latitude && f.longitude).map(f => ({
        lat: f.latitude,
        lon: f.longitude,
        type: 'facility',
        name: f.facility_name,
        facilityType: f.facility_type,
        capacity: f.capacity_kg_per_day,
        area: f.area_name
      })),
      ...highWasteAreas.filter(a => a.latitude && a.longitude).map(a => ({
        lat: a.latitude,
        lon: a.longitude,
        type: 'highwaste',
        name: a.area,
        totalWaste: a.total_waste_kg_per_day,
        wasteBreakdown: {
          wet: a.wet_kg,
          dry: a.dry_kg,
          plastic: a.plastic_kg,
          glass: a.glass_kg,
          metal: a.metal_kg,
          medical: a.medical_kg
        }
      }))
    ]
    
    if (allPoints.length === 0) return
    
    // Find bounds
    const coords = allPoints.map(p => [p.lon, p.lat])
    const minLon = Math.min(...coords.map(c => c[0]))
    const maxLon = Math.max(...coords.map(c => c[0]))
    const minLat = Math.min(...coords.map(c => c[1]))
    const maxLat = Math.max(...coords.map(c => c[1]))
    
    const padding = 0.02
    const lonRange = maxLon - minLon + padding * 2
    const latRange = maxLat - minLat + padding * 2
    
    const project = (lon, lat) => ({
      x: ((lon - (minLon - padding)) / lonRange) * rect.width,
      y: ((maxLat + padding - lat) / latRange) * rect.height
    })
    
    // Draw grid lines
    ctx.strokeStyle = '#1e1e1e'
    ctx.lineWidth = 1
    for (let i = 0; i <= 10; i++) {
      const x = (i / 10) * rect.width
      const y = (i / 10) * rect.height
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, rect.height)
      ctx.moveTo(0, y)
      ctx.lineTo(rect.width, y)
      ctx.stroke()
    }
    
    // Draw points
    allPoints.forEach(point => {
      if (filterType !== 'all' && filterType !== point.type) return
      
      const p = project(point.lon, point.lat)
      
      if (point.type === 'facility') {
        // Facility - square
        let color = '#3b82f6'
        if (point.facilityType?.toLowerCase().includes('biomedical')) color = '#ef4444'
        else if (point.facilityType?.toLowerCase().includes('wet')) color = '#06b6d4'
        else if (point.facilityType?.toLowerCase().includes('plastic')) color = '#f97316'
        else if (point.facilityType?.toLowerCase().includes('glass')) color = '#22c55e'
        else if (point.facilityType?.toLowerCase().includes('metal')) color = '#84cc16'
        else if (point.facilityType?.toLowerCase().includes('landfill')) color = '#a3a3a3'
        
        ctx.fillStyle = color
        ctx.fillRect(p.x - 8, p.y - 8, 16, 16)
        ctx.strokeStyle = '#0a0a0a'
        ctx.lineWidth = 2
        ctx.strokeRect(p.x - 8, p.y - 8, 16, 16)
        
        // Label
        ctx.fillStyle = '#fff'
        ctx.font = '10px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(point.name, p.x, p.y - 14)
        
      } else if (point.type === 'highwaste') {
        // High waste area - circle with size based on waste
        const waste = point.totalWaste || 0
        const radius = Math.min(Math.max(Math.sqrt(waste / 100) * 5, 8), 30)
        
        ctx.beginPath()
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(239, 68, 68, 0.3)'
        ctx.fill()
        ctx.strokeStyle = '#ef4444'
        ctx.lineWidth = 2
        ctx.stroke()
        
        // Center dot
        ctx.beginPath()
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2)
        ctx.fillStyle = '#ef4444'
        ctx.fill()
        
        // Label
        ctx.fillStyle = '#fff'
        ctx.font = '11px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(point.name, p.x, p.y - radius - 8)
        if (waste > 0) {
          ctx.fillStyle = '#ef4444'
          ctx.font = '9px system-ui'
          ctx.fillText(`${Math.round(waste)} kg/day`, p.x, p.y + radius + 12)
        }
      }
    })
  }, [facilities, highWasteAreas, filterType])

  const facilityTypes = [...new Set(facilities.map(f => f.facility_type).filter(Boolean))]
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Admin Map</h1>
          <p className="text-text-secondary mt-1">Facilities and high waste generation areas</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Controls Panel */}
          <GlassCard className="lg:col-span-1">
            <h3 className="font-semibold text-text-primary mb-4">Filters</h3>
            
            <div className="space-y-3 mb-6">
              <label className="glass-label">Layer</label>
              <select 
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="glass-select"
              >
                <option value="all">All</option>
                <option value="facility">Facilities</option>
                <option value="highwaste">High Waste Areas</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium text-text-primary">Facility Types ({facilities.length})</h4>
              <div className="flex flex-wrap gap-2">
                <span 
                  className={`px-2 py-1 rounded-full text-xs font-medium ${filterType === 'all' || filterType === 'facility' ? 'bg-emerald/10 border-emerald/30 text-emerald' : 'bg-glass-white/50 border-glass-border text-text-secondary'}`}
                  onClick={() => setFilterType('facility')}
                  style={{cursor: 'pointer'}}
                >
                  All Facilities ({facilities.length})
                </span>
                {facilityTypes.map(type => (
                  <span 
                    key={type}
                    className={`px-2 py-1 rounded-full text-xs font-medium ${filterType === type ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-glass-white/50 border-glass-border text-text-secondary'}`}
                    onClick={() => setFilterType(type)}
                    style={{cursor: 'pointer'}}
                  >
                    {type} ({facilities.filter(f => f.facility_type === type).length})
                  </span>
                ))}
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-glass-border">
              <h4 className="font-medium text-text-primary">High Waste Areas ({highWasteAreas.length})</h4>
              <div className="space-y-2 mt-2 max-h-64 overflow-y-auto">
                {highWasteAreas.slice(0, 10).map(area => (
                  <div key={area.area} className="p-2 bg-glass-white/50 rounded-glass-sm">
                    <div className="flex justify-between">
                      <span className="font-medium text-text-primary text-sm">{area.area}</span>
                      <span className="text-emerald font-bold text-sm">{area.total_waste_kg_per_day?.toFixed(0) || 0} kg/day</span>
                    </div>
                    <div className="text-xs text-text-secondary mt-1">
                      {area.wet_kg}W {area.dry_kg}D {area.plastic_kg}P {area.glass_kg}G {area.metal_kg}M {area.medical_kg}Med
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
          
          {/* Map Canvas */}
          <GlassCard className="lg:col-span-3 h-[700px]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-text-primary">Map View</h3>
              <div className="flex items-center gap-4 text-sm text-text-secondary">
                <span>Facilities: {facilities.filter(f => filterType === 'all' || filterType === 'facility').length}</span>
                <span>High Waste Areas: {highWasteAreas.filter(f => filterType === 'all' || filterType === 'highwaste').length}</span>
              </div>
            </div>
            <div className="relative h-full bg-matte-black rounded-glass-sm overflow-hidden">
              <canvas 
                ref={canvasRef}
                className="w-full h-full"
                style={{ background: '#0a0a0a' }}
              />
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-matte-black/80">
                  <LoadingState text="Loading map..." />
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