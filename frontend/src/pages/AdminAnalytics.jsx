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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Sector
} from 'recharts'
import { format } from 'date-fns'

export function AdminAnalytics() {
  const { user } = useAuth()
  const [wasteByArea, setWasteByArea] = useState([])
  const [wasteByType, setWasteByType] = useState({})
  const [wasteByAccountType, setWasteByAccountType] = useState({})
  const [wasteTrends, setWasteTrends] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [days, setDays] = useState(30)

  useEffect(() => {
    fetchAllData()
  }, [days])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError('')

      const [
        areaRes,
        typeRes,
        accountTypeRes,
        trendsRes
      ] = await Promise.all([
        api.get('/admin/waste/by-area', { params: { days } }).catch(() => ({ data: [] })),
        api.get('/admin/waste/by-type', { params: { days } }).catch(() => ({ data: {} })),
        api.get('/admin/waste/by-account-type', { params: { days } }).catch(() => ({ data: {} })),
        api.get('/admin/waste/trends', { params: { days } }).catch(() => ({ data: [] })),
      ])

      setWasteByArea(areaRes.data || [])
      setWasteByType(typeRes.data || {})
      setWasteByAccountType(accountTypeRes.data || {})
      setWasteTrends(trendsRes.data || [])
    } catch (err) {
      setError('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading analytics..." />
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
            title="Unable to Load Analytics"
            description={error}
            action={{ label: 'Retry', onClick: fetchAllData }}
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
            <h1 className="text-3xl font-bold text-text-primary">Analytics</h1>
            <p className="text-text-secondary mt-1">Detailed waste analytics and trends</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-text-secondary">Period:</span>
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

        {/* Waste by Type Pie Chart */}
        {Object.keys(wasteByType).length > 0 && (
          <GlassCard className="mb-8">
            <h3 className="font-semibold text-text-primary mb-4">Waste Composition by Type ({days} days)</h3>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={Object.entries(wasteByType).map(([name, value]) => ({ name, value }))}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
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

        {/* Waste Trends Over Time */}
        {wasteTrends.length > 0 && (
          <GlassCard className="mb-8">
            <h3 className="font-semibold text-text-primary mb-4">Daily Waste Collection Trend ({days} days)</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={wasteTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" stroke="#666" fontSize={11} />
                <YAxis stroke="#666" fontSize={11} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e1e1e', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="total_waste_kg" 
                  stroke="#00d46a" 
                  strokeWidth={2}
                  dot={{ fill: '#00d46a', strokeWidth: 2 }}
                  name="Total Waste (kg)"
                />
              </LineChart>
            </ResponsiveContainer>
          </GlassCard>
        )}

        {/* Waste by Account Type */}
        {Object.keys(wasteByAccountType).length > 0 && (
          <GlassCard className="mb-8">
            <h3 className="font-semibold text-text-primary mb-4">Waste by Account Type ({days} days)</h3>
            <ResponsiveContainer width="100%" height={350}>
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

        {/* Top Areas by Waste */}
        {wasteByArea.length > 0 && (
          <GlassCard className="mb-8">
            <h3 className="font-semibold text-text-primary mb-4">Top Areas by Waste Volume ({days} days)</h3>
            <ResponsiveContainer width="100%" height={400}>
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
                <Bar dataKey="glass_kg" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Glass" />
                <Bar dataKey="metal_kg" fill="#ec4899" radius={[4, 4, 0, 0]} name="Metal" />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        )}

        {/* Waste by Area Table */}
        {wasteByArea.length > 0 && (
          <GlassCard>
            <h3 className="font-semibold text-text-primary mb-4">Waste by Area Details ({days} days)</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total (kg)</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Wet</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Dry</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Plastic</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Glass</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Metal</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Medical</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Submissions</th>
                  </tr>
                </thead>
                <tbody>
                  {wasteByArea.map((area) => (
                    <tr key={area.area} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 font-medium text-text-primary">{area.area}</td>
                      <td className="p-4 text-right font-medium text-emerald">{area.total_waste_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.wet_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.dry_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.plastic_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.glass_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.metal_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.medical_kg?.toFixed(1)}</td>
                      <td className="p-4 text-right text-text-secondary">{area.submissions_count}</td>
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