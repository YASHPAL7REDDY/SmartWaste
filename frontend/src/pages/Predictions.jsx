import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  Navbar, 
  LoadingState, 
  EmptyState 
} from '../components'
import { format } from 'date-fns'

const WASTE_TYPE_CONFIG = {
  wet: { label: 'Wet Waste', icon: '💧', color: 'text-blue-400' },
  dry: { label: 'Dry Waste', icon: '📦', color: 'text-gray-400' },
  plastic: { label: 'Plastic Waste', icon: '🥤', color: 'text-yellow-400' },
  glass: { label: 'Glass Waste', icon: '🍾', color: 'text-green-400' },
  metal: { label: 'Metal Waste', icon: '♻️', color: 'text-orange-400' },
  medical: { label: 'Medical Waste', icon: '🏥', color: 'text-red-400' },
}

function formatTimestamp(isoString) {
  if (!isoString) return 'N/A'
  try {
    return format(new Date(isoString), 'MMM d, yyyy h:mm a')
  } catch {
    return 'N/A'
  }
}

function getPercentage(value, total) {
  if (!total || total === 0) return '0%'
  return `${((value / total) * 100).toFixed(1)}%`
}

function getChangeColor(change) {
  if (change > 0) return 'text-red-400'
  if (change < 0) return 'text-emerald-400'
  return 'text-text-secondary'
}

function getChangeLabel(change) {
  if (change > 0) return `+${change.toFixed(1)}%`
  if (change < 0) return `${change.toFixed(1)}%`
  return 'No change'
}

export function Predictions() {
  const { user } = useAuth()
  const [nextDay, setNextDay] = useState(null)
  const [dayAfter, setDayAfter] = useState(null)
  const [todaySubmission, setTodaySubmission] = useState(null)
  const [areaPredictions, setAreaPredictions] = useState([])
  const [overflowRisks, setOverflowRisks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  useEffect(() => {
    fetchPredictions()
  }, [])
  
  const fetchPredictions = async () => {
    try {
      setLoading(true)
      
      const [nextDayRes, dayAfterRes, submissionsRes, areaRes, riskRes] = await Promise.all([
        api.get('/predictions/my/next-day').catch(() => ({ data: null })),
        api.get('/predictions/my/day-after-next').catch(() => ({ data: null })),
        api.get('/waste/my-submissions', { params: { limit: 1 } }).catch(() => ({ data: [] })),
        api.get('/predictions/area', { params: { limit: 20 } }).catch(() => ({ data: [] })),
        api.get('/predictions/overflow-risk', { params: { limit: 20 } }).catch(() => ({ data: [] })),
      ])
      
      setNextDay(nextDayRes.data)
      setDayAfter(dayAfterRes.data)
      
      if (submissionsRes.data && submissionsRes.data.length > 0) {
        const latest = submissionsRes.data[0]
        const detailRes = await api.get(`/waste/submission/${latest.id}`).catch(() => ({ data: null }))
        setTodaySubmission(detailRes.data)
      }
      
      setAreaPredictions(areaRes.data || [])
      setOverflowRisks(riskRes.data || [])
    } catch (err) {
      setError('Failed to load predictions')
    } finally {
      setLoading(false)
    }
  }
  
  const renderPredictionCard = (pred, label) => {
    if (!pred) return null
    
    const total = pred.predicted_waste_kg || 0
    const breakdown = pred.waste_type_breakdown || []
    
    let todayTotal = 0
    const todayBreakdown = {}
    if (todaySubmission) {
      todayTotal = todaySubmission.total_waste_kg || 0
      todaySubmission.items?.forEach(item => {
        todayBreakdown[item.waste_type] = item.quantity_kg
      })
    }
    
    const totalChange = todayTotal > 0 ? ((total - todayTotal) / todayTotal) * 100 : 0
    const changeColor = getChangeColor(totalChange)
    const changeLabel = getChangeLabel(totalChange)
    
    return (
      <GlassCard key={label} className="p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-emerald">{label}</span>
            <span className={`text-sm font-semibold ${changeColor}`}>
              {todayTotal > 0 ? (
                <>
                  <span className="mr-2">vs Today: {todayTotal.toFixed(2)} kg</span>
                  <span>({changeLabel})</span>
                </>
              ) : null}
            </span>
          </div>
          
          <div className="text-4xl font-bold text-text-primary mb-1">
            {total.toFixed(2)} kg
          </div>
          <div className="text-text-secondary text-sm">
            Predicted Total Waste
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          {breakdown.map((item) => {
            const config = WASTE_TYPE_CONFIG[item.waste_type] || { label: item.waste_type, icon: '📦', color: 'text-text-primary' }
            const todayValue = todayBreakdown[item.waste_type] || 0
            const itemChange = todayValue > 0 ? ((item.predicted_kg - todayValue) / todayValue) * 100 : 0
            const itemChangeColor = getChangeColor(itemChange)
            
            return (
              <div key={item.waste_type} className="p-4 bg-glass-white/30 rounded-glass border border-glass-border/50">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{config.icon}</span>
                  <span className="font-medium text-text-primary">{config.label}</span>
                </div>
                <div className="text-2xl font-bold text-text-primary mb-1">
                  {item.predicted_kg.toFixed(2)} kg
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">{getPercentage(item.predicted_kg, total)} of total</span>
                  {todayValue > 0 && (
                    <span className={`font-medium ${itemChangeColor}`}>
                      {getChangeLabel(itemChange)}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        
        <div className="border-t border-glass-border/50 pt-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-secondary">Prediction Date</span>
            <span className="font-medium text-text-primary">{format(new Date(pred.prediction_date), 'MMM d, yyyy')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Horizon</span>
            <span className="font-medium text-text-primary capitalize">{pred.horizon?.replace('_', ' ')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Model Used</span>
            <span className="font-medium text-emerald">{pred.model}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Generated</span>
            <span className="font-medium text-text-primary">{formatTimestamp(pred.created_at)}</span>
          </div>
        </div>
      </GlassCard>
    )
  }
  
  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading predictions..." />
        </div>
      </div>
    )
  }
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Waste Predictions</h1>
          <p className="text-text-secondary mt-1">AI-powered forecasts with explainability</p>
        </div>
        
        {/* Today's Submission Summary */}
        {todaySubmission && (
          <GlassCard className="mb-8 p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Today's Submission</h3>
            <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
              <div className="md:col-span-2">
                <div className="text-text-secondary text-sm">Date</div>
                <div className="font-medium text-text-primary">{format(new Date(todaySubmission.submission_date), 'MMM d, yyyy')}</div>
              </div>
              <div className="md:col-span-2">
                <div className="text-text-secondary text-sm">Total Waste</div>
                <div className="text-2xl font-bold text-text-primary">{todaySubmission.total_waste_kg.toFixed(2)} kg</div>
              </div>
              <div className="md:col-span-3">
                <div className="text-text-secondary text-sm">Breakdown</div>
                <div className="flex flex-wrap gap-2 mt-1">
                  {todaySubmission.items?.map(item => {
                    const config = WASTE_TYPE_CONFIG[item.waste_type] || { icon: '📦', color: 'text-text-primary' }
                    return (
                      <span key={item.waste_type} className={`px-2 py-1 text-xs rounded-full border ${config.color} bg-white/5`}>
                        {config.icon} {item.waste_type}: {item.quantity_kg} kg
                      </span>
                    )
                  })}
                </div>
              </div>
            </div>
          </GlassCard>
        )}
        
        {/* User Predictions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Your Predictions</h2>
          <div className="card-grid">
            {renderPredictionCard(nextDay, 'Tomorrow')}
            {renderPredictionCard(dayAfter, 'Day After Tomorrow')}
          </div>
          
          {!nextDay && !dayAfter && (
            <EmptyState
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
              title="No Predictions Available"
              description="Submit waste data to generate personalized predictions"
              action={{ label: 'Collect Data', onClick: () => navigate('/collect') }}
            />
          )}
        </div>
        
        {/* Area Predictions */}
        {areaPredictions.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary mb-4">Area Predictions</h2>
            <div className="glass-card overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Area</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Date</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total (kg)</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Horizon</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Model</th>
                  </tr>
                </thead>
                <tbody>
                  {areaPredictions.slice(0, 10).map((pred) => (
                    <tr key={pred.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 text-text-primary">{pred.area}</td>
                      <td className="p-4 text-text-secondary">{format(new Date(pred.prediction_date), 'MMM d, yyyy')}</td>
                      <td className="p-4 text-right font-medium text-text-primary">{pred.predicted_waste_kg}</td>
                      <td className="p-4 capitalize text-text-secondary">{pred.horizon}</td>
                      <td className="p-4 text-text-muted">{pred.model}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* Overflow Risks */}
        {overflowRisks.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-4">Overflow Risk Areas</h2>
            <div className="card-grid">
              {overflowRisks.slice(0, 8).map((risk) => (
                <GlassCard key={risk.id} className={risk.risk_level === 'critical' ? 'border-red-500/30' : ''}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-text-primary">{risk.area}</h3>
                    <span className={`
                      px-2 py-0.5 rounded-full text-xs font-medium
                      ${risk.risk_level === 'critical' ? 'bg-red-500/20 text-red-400' :
                        risk.risk_level === 'high' ? 'bg-orange-500/20 text-orange-400' :
                        risk.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'}
                    `}>
                    {risk.risk_level?.toUpperCase() || 'UNKNOWN'}
                  </span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Predicted Total</span>
                      <span className="font-medium text-text-primary">{risk.predicted_total_waste_kg?.toFixed(1) || 'N/A'} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Capacity Utilization</span>
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
      </div>
    </div>
  )
}