import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
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

export function AdminDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [wasteByArea, setWasteByArea] = useState([])
  const [wasteByType, setWasteByType] = useState({})
  const [wasteByAccountType, setWasteByAccountType] = useState({})
  const [facilities, setFacilities] = useState([])
  const [collectorPerformance, setCollectorPerformance] = useState([])
  const [accuracyStats, setAccuracyStats] = useState([])
  const [highWasteAreas, setHighWasteAreas] = useState([])
  const [overflowSummary, setOverflowSummary] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  useEffect(() => {
    fetchAllData()
  }, [])
  
  const fetchAllData = async () => {
    try {
      setLoading(true)
      
      const [
        overviewRes,
        areaRes,
        facilitiesRes,
        accuracyRes,
      ] = await Promise.all([
        api.get('/admin/overview').catch(() => ({ data: null })),
        api.get('/admin/area-waste-analytics', { params: { limit: 20 } }).catch(() => ({ data: { areas: [] } })),
        api.get('/admin/facilities', { params: { limit: 20 } }).catch(() => ({ data: { facilities: [] } })),
        api.get('/admin/prediction-accuracy', { params: { model: 'Ensemble_60XGB_40RF' } }).catch(() => ({ data: { accuracy: [] } })),
      ])
      
      const overview = overviewRes.data || {}
      setStats({
        total_users: overview.total_contributors || 0,
        total_collectors: overview.collector_count || 0,
        total_submissions: overview.total_submissions || 0,
        total_waste_kg: overview.total_waste_submitted_kg || 0,
        total_facilities: facilitiesRes.data?.facilities?.length || 0,
        active_facilities: (facilitiesRes.data?.facilities || []).filter(f => f.status === 'active').length || 0,
      })
      setWasteByArea(overview.waste_by_area || [])
      setWasteByType(overview.waste_by_category || {})
      setWasteByAccountType(overview.waste_by_account_type || {})
      setFacilities(facilitiesRes.data?.facilities || [])
      setAccuracyStats(accuracyRes.data?.accuracy || [])
      setHighWasteAreas(areaRes.data?.areas || [])
      setOverflowSummary({})
      setCollectorPerformance([])
    } catch (err) {
      setError('Failed to load admin dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading admin dashboard..." />
        </div>
      </div>
    )
  }
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Admin Dashboard</h1>
          <p className="text-text-secondary mt-1">Central intelligence view for SmartWaste</p>
        </div>
        
        {/* Stats Overview */}
        {stats && (
          <div className="card-grid mb-8">
            <GlassCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Total Users</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{stats.total_users}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
              </div>
            </GlassCard>
            
            <GlassCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Total Collectors</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{stats.total_collectors}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
            </GlassCard>
            
            <GlassCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Total Submissions</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{stats.total_submissions}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
              </div>
            </GlassCard>
            
            <GlassCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Total Waste (kg)</p>
                  <p className="text-3xl font-bold text-emerald mt-1">{stats.total_waste_kg?.toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-emerald/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
              </div>
            </GlassCard>
            
            <GlassCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Total Facilities</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{stats.total_facilities}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
              </div>
            </GlassCard>
            
            <GlassCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm">Active Facilities</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{stats.active_facilities}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </GlassCard>
          </div>
        )}
        
        {/* Overflow Risk Summary */}
        {Object.keys(overflowSummary).length > 0 && (
          <GlassCard className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Overflow Risk Summary (Today)</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-glass-sm text-center">
                <p className="text-2xl font-bold text-red-400">{overflowSummary.critical || 0}</p>
                <p className="text-sm text-text-secondary">Critical</p>
              </div>
              <div className="p-4 bg-orange-500/10 border border-orange-500/30 rounded-glass-sm text-center">
                <p className="text-2xl font-bold text-orange-400">{overflowSummary.high || 0}</p>
                <p className="text-sm text-text-secondary">High</p>
              </div>
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm text-center">
                <p className="text-2xl font-bold text-yellow-400">{overflowSummary.medium || 0}</p>
                <p className="text-sm text-text-secondary">Medium</p>
              </div>
              <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-glass-sm text-center">
                <p className="text-2xl font-bold text-green-400">{overflowSummary.low || 0}</p>
                <p className="text-sm text-text-secondary">Low</p>
              </div>
              <div className="p-4 bg-emerald/10 border border-emerald/30 rounded-glass-sm text-center">
                <p className="text-2xl font-bold text-emerald">{overflowSummary.total_areas_at_risk || 0}</p>
                <p className="text-sm text-text-secondary">Total at Risk</p>
              </div>
            </div>
          </GlassCard>
        )}
        
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Waste by Type Pie Chart */}
          {Object.keys(wasteByType).length > 0 && (
            <GlassCard className="lg:col-span-1">
              <h3 className="font-semibold text-text-primary mb-4">Waste by Type (30 days)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(wasteByType).map(([name, value]) => ({ name, value }))}
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
                    {Object.entries(wasteByType).map((_, index) => (
                      <Cell key={`cell-${index}`} fill={`hsl(${index * 60}, 70%, 50%)`} />
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
          )}
          
          {/* Waste by Account Type */}
          {Object.keys(wasteByAccountType).length > 0 && (
            <GlassCard className="lg:col-span-1">
              <h3 className="font-semibold text-text-primary mb-4">Waste by Account Type (30 days)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.entries(wasteByAccountType).map(([name, data]) => ({ name, ...data }))}>
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
                  <Bar dataKey="total_waste_kg" fill="#00d46a" radius={[4, 4, 0, 0]} name="Total Waste" />
                  <Bar dataKey="submissions" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Submissions" />
                </BarChart>
              </ResponsiveContainer>
            </GlassCard>
          )}
        </div>
        
        {/* High Waste Areas */}
        {highWasteAreas.length > 0 && (
          <GlassCard className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">High Waste Generation Areas</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">City</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total (kg/day)</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Wet</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Dry</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Plastic</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Glass</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Metal</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Medical</th>
                  </tr>
                </thead>
                <tbody>
                  {highWasteAreas.map((area) => (
                    <tr key={area.area} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 font-medium text-text-primary">{area.area}</td>
                      <td className="p-4 text-text-secondary">{area.city}</td>
                      <td className="p-4 text-right font-medium text-emerald">{area.total_waste_kg_per_day?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.wet_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.dry_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.plastic_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.glass_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.metal_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.medical_kg?.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}
        
        {/* Waste by Area Chart */}
        {wasteByArea.length > 0 && (
          <GlassCard className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Waste by Area (30 days)</h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={wasteByArea.slice(0, 15)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="area" stroke="#666" fontSize={11} angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#666" fontSize={11} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e1e1e', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="total_waste_kg" fill="#00d46a" radius={[4, 4, 0, 0]} name="Total Waste" />
                <Bar dataKey="wet_kg" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Wet" />
                <Bar dataKey="dry_kg" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Dry" />
                <Bar dataKey="plastic_kg" fill="#f97316" radius={[4, 4, 0, 0]} name="Plastic" />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        )}
        
        {/* Collector Performance */}
        {collectorPerformance.length > 0 && (
          <GlassCard className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Collector Performance (30 days)</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Collector ID</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total Collections</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Completed</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Completion Rate</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Predicted (kg)</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Collected (kg)</th>
                  </tr>
                </thead>
                <tbody>
                  {collectorPerformance.map((collector) => (
                    <tr key={collector.collector_id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 font-mono text-text-primary">{collector.collector_id.slice(0, 16)}...</td>
                      <td className="p-4 text-right text-text-primary">{collector.total_collections}</td>
                      <td className="p-4 text-right text-text-primary">{collector.completed}</td>
                      <td className="p-4 text-right font-medium text-emerald">
                        {collector.total_collections > 0 ? ((collector.completed / collector.total_collections) * 100).toFixed(1) : 0}%
                      </td>
                      <td className="p-4 text-right text-text-secondary">{collector.total_predicted?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{collector.total_collected?.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}
        
        {/* Facilities */}
        {facilities.length > 0 && (
          <GlassCard>
            <h2 className="text-xl font-semibold text-text-primary mb-4">Facilities Overview</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Facility</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Type</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Capacity (kg/day)</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {facilities.slice(0, 20).map((facility) => (
                    <tr key={facility.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 font-medium text-text-primary">{facility.facility_name}</td>
                      <td className="p-4 text-text-secondary">{facility.facility_type}</td>
                      <td className="p-4 text-text-secondary">{facility.area_name}</td>
                      <td className="p-4 text-right text-text-secondary">
                        {facility.capacity_kg_per_day ? facility.capacity_kg_per_day.toLocaleString() : 'Unknown'}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          facility.status === 'active' ? 'bg-green-500/20 text-green-400' :
                          facility.status === 'inactive' ? 'bg-red-500/20 text-red-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {facility.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {facilities.length > 20 && (
              <p className="text-sm text-text-muted mt-4 text-center">Showing 20 of {facilities.length} facilities</p>
            )}
          </GlassCard>
        )}
      </div>
    </div>
  )
}