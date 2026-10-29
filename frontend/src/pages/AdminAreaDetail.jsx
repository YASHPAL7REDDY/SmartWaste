import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  Navbar, 
  LoadingState,
  EmptyState
} from '../components'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Sector
} from 'recharts'
import { format } from 'date-fns'

export function AdminAreaDetail() {
  const { isAuthenticated, role } = useAuth()
  const { area } = useParams()
  const [areaData, setAreaData] = useState(null)
  const [areaSubmissions, setAreaSubmissions] = useState([])
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [timeRange, setTimeRange] = useState('30')
  
  if (!isAuthenticated || role !== 'admin') {
    return <Navigate to="/" replace />
  }

  const fetchAreaData = async () => {
    setLoading(true)
    setError('')
    try {
      const [submissionsRes, predictionsRes, areaStatsRes] = await Promise.all([
        api.get('/admin/waste/by-area', { params: { days: parseInt(timeRange) } }),
        api.get('/admin/predictions/by-type', { params: { area, limit: 50 } }),
        api.get('/admin/high-waste-areas', { params: { limit: 50 } })
      ])
      
      const allSubmissions = submissionsRes.data || []
      const areaSubmissions = allSubmissions.find(s => s.area === area)
      const areaPred = predictionsRes.data || []
      const areaHighWaste = areaStatsRes.data || []
      const areaZone = areaHighWaste.find(z => z.area === area)
      
      setAreaData({ submissions: areaSubmissions, zone: areaZone })
      setAreaSubmissions(areaSubmissions ? [areaSubmissions] : [])
      setPredictions(areaPred)
    } catch (err) {
      setError('Failed to load area data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAreaData()
  }, [area, timeRange])

  const timeRangeOptions = [
    { value: '7', label: '7 Days' },
    { value: '30', label: '30 Days' },
    { value: '90', label: '90 Days' },
    { value: '365', label: '1 Year' }
  ]

  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading area data..." />
        </div>
      </div>
    )
  }

  if (error || !areaData?.submissions) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container max-w-3xl">
          <Link to="/admin" className="text-emerald hover:underline mb-6 inline-block">
            ← Back to Admin Dashboard
          </Link>
          <EmptyState
            title="Area Not Found"
            description={error || `No data available for ${area}`}
          />
        </div>
      </div>
    )
  }

  const { submissions, zone } = areaData
  const sub = submissions?.[0] || {}
  const wasteTypes = [
    { key: 'wet_kg', label: 'Wet', color: '#3b82f6' },
    { key: 'dry_kg', label: 'Dry', color: '#f59e0b' },
    { key: 'plastic_kg', label: 'Plastic', color: '#f97316' },
    { key: 'glass_kg', label: 'Glass', color: '#22c55e' },
    { key: 'metal_kg', label: 'Metal', color: '#84cc16' },
    { key: 'medical_kg', label: 'Medical', color: '#ef4444' }
  ]

  const chartData = wasteTypes.map(wt => ({
    name: wt.label,
    value: sub[wt.key] || 0,
    color: wt.color
  }))

  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <Link to="/admin" className="text-emerald hover:underline">
            ← Back to Admin Dashboard
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-text-secondary">Time Range:</span>
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="glass-select w-auto"
            >
              {timeRangeOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">{area}</h1>
          <p className="text-text-secondary mt-1">
            {zone?.city || 'Unknown City'} • {sub.submissions_count || 0} submissions • {sub.total_waste_kg} kg total waste
          </p>
        </div>
        
        {/* Summary Cards */}
        <div className="card-grid mb-8">
          {wasteTypes.map(wt => (
            <GlassCard key={wt.key}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">{wt.label}</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{sub[wt.key]?.toFixed(2) || 0} kg</p>
                </div>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center`} style={{ backgroundColor: `${wt.color}20` }}>
                  <svg className="w-6 h-6" style={{ color: wt.color }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
        
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Pie Chart */}
          <GlassCard className="lg:col-span-1">
            <h3 className="font-semibold text-text-primary mb-4">Waste Composition</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData.filter(d => d.value > 0)}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  labelLine={false}
                >
                  {chartData.filter(d => d.value > 0).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartData[index].color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e1e1e', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </GlassCard>
          
          {/* Bar Chart */}
          <GlassCard className="lg:col-span-1">
            <h3 className="font-semibold text-text-primary mb-4">Waste by Type (kg)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.filter(d => d.value > 0)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="name" stroke="#666" fontSize={11} />
                <YAxis stroke="#666" fontSize={11} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e1e1e', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.filter(d => d.value > 0).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartData[index].color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </div>
        
        {/* Zone Data */}
        {zone && (
          <GlassCard className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Zone Generation Data</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-text-secondary text-sm">Total Generation</p>
                <p className="text-2xl font-bold text-emerald mt-1">{zone.total_waste_kg_per_day?.toFixed(1) || 0} kg/day</p>
              </div>
              <div>
                <p className="text-text-secondary text-sm">Household</p>
                <p className="text-xl font-bold text-text-primary mt-1">{zone.household_waste_kg_per_day?.toFixed(1) || 0} kg/day</p>
              </div>
              <div>
                <p className="text-text-secondary text-sm">Commercial</p>
                <p className="text-xl font-bold text-text-primary mt-1">{zone.commercial_waste_kg_per_day?.toFixed(1) || 0} kg/day</p>
              </div>
              <div>
                <p className="text-text-secondary text-sm">Bulk Generator</p>
                <p className="text-xl font-bold text-text-primary mt-1">{zone.bulk_generator_waste_kg_per_day?.toFixed(1) || 0} kg/day</p>
              </div>
            </div>
            
            <div className="mt-4 grid grid-cols-2 md:grid-cols-6 gap-4 pt-4 border-t border-glass-border">
              {wasteTypes.map(wt => (
                <div key={wt.key} className="text-center">
                  <p className="text-text-secondary text-sm capitalize">{wt.label}</p>
                  <p className="text-xl font-bold text-text-primary mt-1">{zone[wt.key]?.toFixed(1) || 0} kg/day</p>
                </div>
              ))}
            </div>
            
            {zone.data_quality_notes && (
              <p className="text-text-muted text-sm mt-4">{zone.data_quality_notes}</p>
            )}
          </GlassCard>
        )}
        
        {/* Predictions */}
        {predictions.length > 0 && (
          <GlassCard className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Area Predictions</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Date</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Horizon</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total (kg)</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Wet</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Dry</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Plastic</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Glass</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Metal</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Medical</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Model</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.slice(0, 20).map((pred) => (
                    <tr key={pred.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 text-text-secondary">{format(new Date(pred.prediction_date), 'MMM d, yyyy')}</td>
                      <td className="p-4 capitalize text-text-secondary">{pred.horizon}</td>
                      <td className="p-4 text-right font-medium text-text-primary">{pred.predicted_waste_kg}</td>
                      <td className="p-4 text-right text-text-secondary">{pred.wet_predicted_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{pred.dry_predicted_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{pred.plastic_predicted_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{pred.glass_predicted_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{pred.metal_predicted_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{pred.medical_predicted_kg?.toFixed(1)}</td>
                      <td className="p-4 text-text-muted">{pred.model}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}
        
      </div>
    </div>
  )
}

import { Navigate } from 'react-router-dom'