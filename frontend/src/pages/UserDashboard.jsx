import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  LoadingState, 
  EmptyState, 
  Navbar 
} from '../components'
import { format } from 'date-fns'

export function UserDashboard() {
  const { user, role } = useAuth()
  const [stats, setStats] = useState(null)
  const [recentSubmissions, setRecentSubmissions] = useState([])
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  useEffect(() => {
    fetchDashboardData()
  }, [])
  
  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch recent submissions
      const submissionsRes = await api.get('/waste/my-submissions', { params: { limit: 5 } })
      const submissions = submissionsRes.data || []
      setRecentSubmissions(submissions)
      
      // Fetch predictions
      const [nextDayRes, dayAfterRes] = await Promise.all([
        api.get('/predictions/my/next-day').catch(() => ({ data: null })),
        api.get('/predictions/my/day-after-next').catch(() => ({ data: null })),
      ])
      
      const preds = []
      if (nextDayRes.data) preds.push({ ...nextDayRes.data, horizon: 'Tomorrow' })
      if (dayAfterRes.data) preds.push({ ...dayAfterRes.data, horizon: 'Day After Tomorrow' })
      setPredictions(preds)
      
      // Calculate stats
      const totalSubmissions = submissions.length
      const totalWaste = submissions.reduce((sum, s) => sum + (s.total_waste_kg || 0), 0)
      const todayWaste = submissions
        .filter(s => s.submission_date === format(new Date(), 'yyyy-MM-dd'))
        .reduce((sum, s) => sum + (s.total_waste_kg || 0), 0)
      
      setStats({
        totalSubmissions,
        totalWaste: totalWaste.toFixed(2),
        todayWaste: todayWaste.toFixed(2),
      })
    } catch (err) {
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading dashboard..." />
        </div>
      </div>
    )
  }
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Welcome, {user?.name}</h1>
          <p className="text-text-secondary mt-1">Here's your waste management overview</p>
        </div>
        
        {/* Stats Grid */}
        <div className="card-grid mb-8">
          <GlassCard>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">Today's Waste</p>
                <p className="text-3xl font-bold text-emerald mt-1">{stats?.todayWaste || 0} kg</p>
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
                <p className="text-text-secondary text-sm">Total Submissions</p>
                <p className="text-3xl font-bold text-text-primary mt-1">{stats?.totalSubmissions || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
            </div>
          </GlassCard>
          
          <GlassCard>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">Total Waste Submitted</p>
                <p className="text-3xl font-bold text-text-primary mt-1">{stats?.totalWaste || 0} kg</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </GlassCard>
          
          <GlassCard>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-secondary text-sm">Your Area</p>
                <p className="text-3xl font-bold text-text-primary mt-1">{user?.area || 'Not set'}</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
          </GlassCard>
        </div>
        
        {/* Predictions */}
        {(predictions || []).length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Waste Predictions</h2>
            <div className="card-grid">
              {(predictions || []).map((pred, i) => (
                <GlassCard key={i}>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-medium text-emerald">{pred.horizon}</span>
                    <span className="text-2xl font-bold text-text-primary">{pred.predicted_waste_kg} kg</span>
                  </div>
                  <div className="space-y-2">
                    {pred.waste_type_breakdown.map((item) => (
                      <div key={item.waste_type} className="flex justify-between text-sm">
                        <span className="capitalize text-text-secondary">{item.waste_type}</span>
                        <span className="font-medium text-text-primary">{item.predicted_kg} kg</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-text-muted mt-3">Model: {pred.model}</p>
                </GlassCard>
              ))}
            </div>
          </div>
        )}
        
        {/* Recent Submissions */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-text-primary">Recent Submissions</h2>
            <Link to="/my-data" className="text-sm text-emerald hover:underline">View All</Link>
          </div>
          
          {(recentSubmissions || []).length > 0 ? (
            <div className="glass-card overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Date</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Waste Types</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentSubmissions.map((sub) => (
                    <tr key={sub.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 text-text-primary">{format(new Date(sub.submission_date), 'MMM d, yyyy')}</td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-2">
                          {(sub.waste_types || []).map((wt) => (
                            <span key={wt} className="px-2 py-0.5 rounded text-xs bg-glass-white-strong border border-glass-border text-text-secondary">
                              {wt}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-4 text-right font-medium text-text-primary">{sub.total_waste_kg} kg</td>
                      <td className="p-4">
                        <span className={`
                          px-2 py-1 rounded-full text-xs font-medium
                          ${sub.collection_status === 'collected' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}
                        `}>
                          {sub.collection_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
              title="No Submissions Yet"
              description="Start by submitting your waste data"
              action={{ label: 'Collect Data', onClick: () => navigate('/collect') }}
            />
          )}
        </div>
        
        {/* Quick Actions */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-4">
            <Link to="/collect">
              <GlassButton variant="primary" className="flex-1 min-w-[200px]">
                Submit Waste Data
              </GlassButton>
            </Link>
            <Link to="/my-data">
              <GlassButton variant="default" className="flex-1 min-w-[200px]">
                View My Data
              </GlassButton>
            </Link>
            <Link to="/predictions">
              <GlassButton variant="default" className="flex-1 min-w-[200px]">
                View Predictions
              </GlassButton>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}