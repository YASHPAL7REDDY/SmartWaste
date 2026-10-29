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
  LineChart,
  Line,
  Legend
} from 'recharts'

export function AdminMLPerformance() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState(null)
  const [realWorldMetrics, setRealWorldMetrics] = useState(null)
  const [evalStatus, setEvalStatus] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [selectedWasteType, setSelectedWasteType] = useState('total')
  const [loading, setLoading] = useState(true)
  const [loadingRealWorld, setLoadingRealWorld] = useState(true)
  const [loadingEvalStatus, setLoadingEvalStatus] = useState(true)
  const [loadingChart, setLoadingChart] = useState(false)
  const [error, setError] = useState('')

  const [mlHealth, setMlHealth] = useState(null)
  const [dataDrift, setDataDrift] = useState(null)
  const [performanceTrend, setPerformanceTrend] = useState(null)
  const [modelComparison, setModelComparison] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [loadingHealth, setLoadingHealth] = useState(true)
  const [loadingDrift, setLoadingDrift] = useState(true)
  const [loadingPerfTrend, setLoadingPerfTrend] = useState(true)
  const [loadingModelComp, setLoadingModelComp] = useState(true)
  const [loadingRecommendations, setLoadingRecommendations] = useState(true)
  
  useEffect(() => {
    fetchMetrics()
    fetchRealWorldMetrics()
    fetchEvalStatus()
    fetchMlHealth()
    fetchDataDrift()
    fetchPerformanceTrend()
    fetchModelComparison()
    fetchFullReport()
  }, [])
  
  useEffect(() => {
    fetchChartData()
  }, [selectedWasteType])
  
  const fetchMetrics = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/ml-performance')
      setMetrics(response.data)
    } catch (err) {
      setError('Failed to load ML performance metrics')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }
  
  const fetchRealWorldMetrics = async () => {
    try {
      setLoadingRealWorld(true)
      const response = await api.get('/admin/ml-performance/real-world-accuracy', { params: { days: 30 } })
      setRealWorldMetrics(response.data)
    } catch (err) {
      console.error('Failed to load real-world accuracy metrics:', err)
    } finally {
      setLoadingRealWorld(false)
    }
  }
  
  const fetchEvalStatus = async () => {
    try {
      setLoadingEvalStatus(true)
      const response = await api.get('/admin/ml-performance/evaluation-status', { params: { days: 30 } })
      setEvalStatus(response.data)
    } catch (err) {
      console.error('Failed to load evaluation status:', err)
    } finally {
      setLoadingEvalStatus(false)
    }
  }
  
  const fetchChartData = async () => {
    try {
      setLoadingChart(true)
      const response = await api.get('/admin/ml-performance/actual-vs-predicted', { 
        params: { days: 30, waste_type: selectedWasteType } 
      })
      setChartData(response.data)
    } catch (err) {
      console.error('Failed to load chart data:', err)
      setChartData({ available: false, data: [] })
    } finally {
      setLoadingChart(false)
    }
  }

  const fetchMlHealth = async () => {
    try {
      setLoadingHealth(true)
      const response = await api.get('/admin/ml-monitoring/health')
      setMlHealth(response.data)
    } catch (err) {
      console.error('Failed to load ML health:', err)
    } finally {
      setLoadingHealth(false)
    }
  }

  const fetchDataDrift = async () => {
    try {
      setLoadingDrift(true)
      const response = await api.get('/admin/ml-monitoring/data-drift')
      setDataDrift(response.data)
    } catch (err) {
      console.error('Failed to load data drift:', err)
    } finally {
      setLoadingDrift(false)
    }
  }

  const fetchPerformanceTrend = async () => {
    try {
      setLoadingPerfTrend(true)
      const response = await api.get('/admin/ml-monitoring/performance-trend')
      setPerformanceTrend(response.data)
    } catch (err) {
      console.error('Failed to load performance trend:', err)
    } finally {
      setLoadingPerfTrend(false)
    }
  }

  const fetchModelComparison = async () => {
    try {
      setLoadingModelComp(true)
      const response = await api.get('/admin/ml-monitoring/model-comparison')
      setModelComparison(response.data)
    } catch (err) {
      console.error('Failed to load model comparison:', err)
    } finally {
      setLoadingModelComp(false)
    }
  }

  const fetchFullReport = async () => {
    try {
      setLoadingRecommendations(true)
      const response = await api.get('/admin/ml-monitoring/full-report')
      if (response.data.recommendations) {
        setRecommendations(response.data.recommendations)
      }
    } catch (err) {
      console.error('Failed to load full report:', err)
    } finally {
      setLoadingRecommendations(false)
    }
  }

  const formatMetric = (value) => {
    if (value === "N/A" || value === null || value === undefined) return "N/A"
    if (typeof value === 'number') return value.toFixed(4)
    return value
  }
  
  const getMetricColor = (value) => {
    if (value === "N/A") return "text-text-muted"
    if (typeof value !== 'number') return "text-text-muted"
    if (value >= 0.8) return "text-emerald-400"
    if (value >= 0.6) return "text-yellow-400"
    if (value >= 0.4) return "text-orange-400"
    return "text-red-400"
  }
  
  const getErrorColor = (value) => {
    if (value === "N/A") return "text-text-muted"
    if (typeof value !== 'number') return "text-text-muted"
    if (value <= 5) return "text-emerald-400"
    if (value <= 15) return "text-yellow-400"
    if (value <= 30) return "text-orange-400"
    return "text-red-400"
  }
  
  const formatMAPE = (value) => {
    if (value === "N/A") return "N/A"
    if (typeof value === 'number' && value > 100) return "N/A"
    if (typeof value === 'number') return value.toFixed(1) + "%"
    return value
  }
  
  const formatAccuracy = (r2) => {
    if (r2 === "N/A" || r2 === null || r2 === undefined) return "N/A"
    if (typeof r2 === 'number') {
      if (r2 < 0) return "N/A"
      return (r2 * 100).toFixed(1) + "%"
    }
    return r2
  }
  
  const formatCount = (value) => {
    if (value === "N/A" || value === null || value === undefined) return "N/A"
    if (typeof value === 'number') return value.toLocaleString()
    return value
  }

  const getDriftStatusColor = (status) => {
    switch (status) {
      case 'NO_DRIFT': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 'MODERATE_DRIFT': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'HIGH_DRIFT': return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'INSUFFICIENT_DATA': return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      case 'NOT_CALCULATED': return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'ERROR': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  const getHealthStatusColor = (status) => {
    switch (status) {
      case 'HEALTHY': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 'WARNING': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'INSUFFICIENT_DATA': return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  const getReliabilityColor = (level) => {
    switch (level) {
      case 'STRONG_EVALUATION': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
      case 'MODERATE_CONFIDENCE': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      case 'EARLY_EVALUATION': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      case 'INSUFFICIENT_DATA': return 'text-red-400 bg-red-500/10 border-red-500/30'
      default: return 'text-text-muted bg-gray-500/10 border-gray-500/30'
    }
  }

  const getReliabilityLabel = (level) => {
    switch (level) {
      case 'STRONG_EVALUATION': return '🟢 Strong Evaluation'
      case 'MODERATE_CONFIDENCE': return '🟡 Moderate Confidence'
      case 'EARLY_EVALUATION': return '🟡 Early Evaluation'
      case 'INSUFFICIENT_DATA': return '🔴 Insufficient Data'
      default: return '⚪ Unknown'
    }
  }

  const getDriftStatusLabel = (status) => {
    switch (status) {
      case 'NO_DRIFT': return '🟢 No Drift'
      case 'MODERATE_DRIFT': return '🟡 Moderate Drift'
      case 'HIGH_DRIFT': return '🔴 High Drift'
      case 'INSUFFICIENT_DATA': return '⚪ Insufficient Data'
      case 'NOT_CALCULATED': return '⚪ Not Calculated'
      case 'ERROR': return '🔴 Error'
      default: return '⚪ Unknown'
    }
  }

  const getHealthStatusLabel = (status) => {
    switch (status) {
      case 'HEALTHY': return '🟢 Healthy'
      case 'WARNING': return '🟡 Warning'
      case 'CRITICAL': return '🔴 Critical'
      case 'INSUFFICIENT_DATA': return '⚪ Insufficient Data'
      default: return '⚪ Unknown'
    }
  }
  
  if (loading) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <LoadingState text="Loading ML performance metrics..." />
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <EmptyState
            title="Unable to Load Metrics"
            description={error}
            action={{ label: 'Retry', onClick: fetchMetrics }}
          />
        </div>
      </div>
    )
  }
  
  if (!metrics) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container">
          <EmptyState title="No Metrics Available" />
        </div>
      </div>
    )
  }
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">ML Model Performance</h1>
          <p className="text-text-secondary mt-1">Evaluation metrics for SmartWaste prediction models</p>
        </div>
        
        {/* SECTION 1: MODEL OVERVIEW */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Model Overview</h2>
          <div className="card-grid">
            {Object.entries(metrics.model_overview || {}).map(([modelId, model]) => (
              <GlassCard key={modelId} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-text-primary">{model.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    model.status === "Evaluated" ? "bg-emerald-500/20 text-emerald-400" : "bg-yellow-500/20 text-yellow-400"
                  }`}>
                    {model.status}
                  </span>
                </div>
                <div className="text-sm text-text-secondary mb-3">{model.type}</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-text-secondary text-xs">R²</div>
                    <div className={`text-2xl font-bold ${getMetricColor(model.R2)}`}>{formatMetric(model.R2)}</div>
                  </div>
                  <div>
                    <div className="text-text-secondary text-xs">MAE (kg)</div>
                    <div className="text-2xl font-bold text-text-primary">{formatMetric(model.MAE)}</div>
                  </div>
                  <div>
                    <div className="text-text-secondary text-xs">RMSE (kg)</div>
                    <div className="text-2xl font-bold text-text-primary">{formatMetric(model.RMSE)}</div>
                  </div>
                  <div>
                    <div className="text-text-secondary text-xs">SMAPE</div>
                    <div className="text-2xl font-bold text-text-primary">{formatMAPE(model.SMAPE)}</div>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
        
        {/* SECTION 2: WASTE TYPE PERFORMANCE */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Waste Type Performance (Test Set)</h2>
          <div className="glass-card overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-glass-border">
                  <th className="text-left p-4 text-sm font-medium text-text-secondary">Waste Type</th>
                  <th className="text-right p-4 text-sm font-medium text-text-secondary">R²</th>
                  <th className="text-right p-4 text-sm font-medium text-text-secondary">MAE (kg)</th>
                  <th className="text-right p-4 text-sm font-medium text-text-secondary">RMSE (kg)</th>
                  <th className="text-right p-4 text-sm font-medium text-text-secondary">MAPE</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.waste_type_performance || {}).map(([wt, data]) => (
                  <tr key={wt} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                    <td className="p-4 font-medium text-text-primary">{data.waste_type}</td>
                    <td className="p-4 text-right">
                      <span className={getMetricColor(data.R2)}>{formatMetric(data.R2)}</span>
                    </td>
                    <td className="p-4 text-right text-text-primary">{formatMetric(data.MAE)}</td>
                    <td className="p-4 text-right text-text-primary">{formatMetric(data.RMSE)}</td>
                    <td className="p-4 text-right text-text-secondary">{formatMAPE(data.MAPE)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* SECTION 3: MODEL COMPARISON */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Model Comparison</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(metrics.model_comparison || {}).map(([metric, models]) => (
              <GlassCard key={metric} className="p-6">
                <h3 className="font-semibold text-text-primary mb-4 capitalize">{metric.toLowerCase()}</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={Object.entries(models).map(([id, m]) => ({ name: m.name, value: typeof m.value === 'number' ? m.value : 0 }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="name" stroke="#666" fontSize={11} angle={-20} textAnchor="end" height={60} />
                    <YAxis stroke="#666" fontSize={11} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e1e1e', 
                        border: '1px solid #333',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {Object.entries(models).map((_, index) => (
                        <Cell key={`cell-${index}`} fill="url(#emeraldGradient)" />
                      ))}
                    </Bar>
                    <defs>
                      <linearGradient id="emeraldGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d46a" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#00d46a" stopOpacity={0.2}/>
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 text-xs text-text-secondary">
                  Higher is better {metric === "MAE" || metric === "RMSE" ? "(lower is better)" : ""}
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
        
        {/* SECTION 4: ACTUAL VS PREDICTED */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Actual vs Predicted Analysis</h2>
          <GlassCard className="p-6 text-center">
            <svg className="w-16 h-16 mx-auto text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-text-secondary">{metrics.actual_vs_predicted?.message || "Actual vs Predicted analysis will appear after sufficient matched collection data is available."}</p>
          </GlassCard>
        </div>
        
        {/* SECTION 5: MODEL INSIGHTS */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Model Insights</h2>
          <div className="card-grid">
            <GlassCard className="p-6">
              <div className="text-text-secondary text-sm mb-1">Best Performing Model</div>
              <div className="text-2xl font-bold text-emerald-400">{metrics.model_insights?.best_performing_model || "N/A"}</div>
            </GlassCard>
            <GlassCard className="p-6">
              <div className="text-text-secondary text-sm mb-1">Strongest Category</div>
              <div className="text-2xl font-bold text-emerald-400">{metrics.model_insights?.strongest_category || "N/A"}</div>
            </GlassCard>
            <GlassCard className="p-6">
              <div className="text-text-secondary text-sm mb-1">Weakest Category</div>
              <div className="text-2xl font-bold text-red-400">{metrics.model_insights?.weakest_category || "N/A"}</div>
            </GlassCard>
            <GlassCard className="p-6">
              <div className="text-text-secondary text-sm mb-1">Total Waste R²</div>
              <div className="text-2xl font-bold text-text-primary">{formatMetric(metrics.model_insights?.total_waste_r2)}</div>
            </GlassCard>
          </div>
        </div>
        
        {/* SECTION 6: PROJECT ML SUMMARY */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Project ML Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GlassCard className="p-6">
              <h3 className="font-semibold text-text-primary mb-4">Dataset</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Train Samples</span>
                  <span className="font-medium text-text-primary">{metrics.project_summary?.dataset_rows?.train || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Validation Samples</span>
                  <span className="font-medium text-text-primary">{metrics.project_summary?.dataset_rows?.validation || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Test Samples</span>
                  <span className="font-medium text-text-primary">{metrics.project_summary?.dataset_rows?.test || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Total Samples</span>
                  <span className="font-bold text-emerald">{metrics.project_summary?.dataset_rows?.total || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Features</span>
                  <span className="font-medium text-text-primary">{metrics.project_summary?.feature_count || "N/A"}</span>
                </div>
              </div>
            </GlassCard>
            
            <GlassCard className="p-6">
              <h3 className="font-semibold text-text-primary mb-4">Methodology</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-text-secondary">Training Approach</div>
                  <div className="text-text-primary mt-1">{metrics.project_summary?.training_approach || "N/A"}</div>
                </div>
                <div>
                  <div className="text-text-secondary">Validation Approach</div>
                  <div className="text-text-primary mt-1">{metrics.project_summary?.validation_approach || "N/A"}</div>
                </div>
                <div>
                  <div className="text-text-secondary">Test Approach</div>
                  <div className="text-text-primary mt-1">{metrics.project_summary?.test_approach || "N/A"}</div>
                </div>
                <div>
                  <div className="text-text-secondary">Prediction Horizons</div>
                  <div className="text-text-primary mt-1">
                    {Array.isArray(metrics.project_summary?.prediction_horizons) 
                      ? metrics.project_summary.prediction_horizons.join(", ") 
                      : "N/A"}
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>
          
          <GlassCard className="mt-6 p-6">
            <h3 className="font-semibold text-text-primary mb-2">Evaluation Note</h3>
            <p className="text-text-secondary text-sm">
              {metrics.project_summary?.evaluation_note || "Metrics computed on hold-out test set with chronological ordering."}
            </p>
          </GlassCard>
        </div>
        
        {/* SECTION 7: REAL-WORLD PREDICTION ACCURACY */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">Real-World Prediction Accuracy</h2>
          
          {/* Evaluation Status & Coverage */}
          {!loadingEvalStatus && evalStatus && (
            <div className="mb-6">
              <GlassCard className="p-6 border-l-4 border-blue-400">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                  <h3 className="font-semibold text-text-primary">Evaluation Coverage</h3>
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400">
                      Coverage: {evalStatus.coverage?.coverage_pct || 0}%
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Total Predictions</div>
                    <div className="text-2xl font-bold text-text-primary">{evalStatus.predictions?.total || 0}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Evaluated</div>
                    <div className="text-2xl font-bold text-emerald-400">{evalStatus.predictions?.evaluated || 0}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Unmatched</div>
                    <div className="text-2xl font-bold text-red-400">{evalStatus.predictions?.unmatched || 0}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Pending</div>
                    <div className="text-2xl font-bold text-yellow-400">{evalStatus.predictions?.pending || 0}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Total Collections</div>
                    <div className="text-2xl font-bold text-text-primary">{evalStatus.collections?.total || 0}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Matched</div>
                    <div className="text-2xl font-bold text-emerald-400">{evalStatus.collections?.matched || 0}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Unmatched</div>
                    <div className="text-2xl font-bold text-red-400">{evalStatus.collections?.unmatched || 0}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Accuracy Records</div>
                    <div className="text-2xl font-bold text-purple-400">{evalStatus.accuracy_records || 0}</div>
                  </div>
                </div>
                {evalStatus.unmatched_reasons && Object.keys(evalStatus.unmatched_reasons).length > 0 && (
                  <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm">
                    <div className="text-yellow-400 text-sm font-medium mb-2">Unmatched Reasons:</div>
                    <div className="flex flex-wrap gap-4 text-sm text-text-secondary">
                      {Object.entries(evalStatus.unmatched_reasons).map(([reason, count]) => (
                        <span key={reason}>{reason}: {count}</span>
                      ))}
                    </div>
                  </div>
                )}
              </GlassCard>
            </div>
          )}
          
          {loadingRealWorld ? (
            <GlassCard className="p-6 text-center">
              <LoadingState text="Loading real-world accuracy data..." />
            </GlassCard>
          ) : (!realWorldMetrics || !realWorldMetrics.available) ? (
            <GlassCard className="p-6 text-center">
              <svg className="w-16 h-16 mx-auto text-text-muted mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-text-secondary">
                {realWorldMetrics?.message || "No matched prediction-actual data available yet. Complete collections to see real-world accuracy."}
              </p>
            </GlassCard>
          ) : (
            <>
              {/* Summary Cards */}
              <div className="card-grid mb-6">
                <GlassCard className="p-6 border-l-4 border-emerald-400">
                  <div className="text-text-secondary text-sm mb-1">Predictions Evaluated</div>
                  <div className="text-3xl font-bold text-emerald-400">{formatCount(realWorldMetrics.predictions_evaluated)}</div>
                </GlassCard>
                <GlassCard className="p-6 border-l-4 border-blue-400">
                  <div className="text-text-secondary text-sm mb-1">Total Predicted</div>
                  <div className="text-3xl font-bold text-text-primary">{realWorldMetrics.total_predicted_kg?.toFixed(1) || 0} kg</div>
                </GlassCard>
                <GlassCard className="p-6 border-l-4 border-purple-400">
                  <div className="text-text-secondary text-sm mb-1">Total Actual</div>
                  <div className="text-3xl font-bold text-text-primary">{realWorldMetrics.total_actual_kg?.toFixed(1) || 0} kg</div>
                </GlassCard>
                <GlassCard className="p-6 border-l-4 border-yellow-400">
                  <div className="text-text-secondary text-sm mb-1">Overall MAE</div>
                  <div className="text-3xl font-bold text-text-primary">{formatMetric(realWorldMetrics.overall_mae_kg)} kg</div>
                </GlassCard>
                <GlassCard className="p-6 border-l-4 border-orange-400">
                  <div className="text-text-secondary text-sm mb-1">Overall RMSE</div>
                  <div className="text-3xl font-bold text-text-primary">{formatMetric(realWorldMetrics.overall_rmse_kg)} kg</div>
                </GlassCard>
              </div>
              
              {/* Data Quality Warning */}
              {(() => {
                const totalSamples = Object.values(realWorldMetrics.by_waste_type || {})
                  .reduce((sum, data) => sum + (data.sample_count || 0), 0);
                const overallReliability = totalSamples < 6 ? "INSUFFICIENT_DATA" :
                                         totalSamples < 21 ? "EARLY_EVALUATION" :
                                         totalSamples < 51 ? "MODERATE_CONFIDENCE" : "STRONG_EVALUATION";
                
                const warnings = {
                  "INSUFFICIENT_DATA": { 
                    label: "Insufficient Data", 
                    msg: "Insufficient real-world samples. Accuracy metrics should not be considered reliable yet.",
                    color: "text-red-400", bg: "bg-red-500/10 border-red-500/30"
                  },
                  "EARLY_EVALUATION": { 
                    label: "Early Evaluation", 
                    msg: "Early evaluation. Continue collecting real-world data.",
                    color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/30"
                  },
                  "MODERATE_CONFIDENCE": { 
                    label: "Moderate Confidence", 
                    msg: "Moderate evaluation confidence.",
                    color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/30"
                  },
                  "STRONG_EVALUATION": { 
                    label: "Strong Evaluation", 
                    msg: "Strong evaluation confidence.",
                    color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30"
                  }
                };
                const w = warnings[overallReliability];
                return (
                  <div className={`p-4 mb-6 rounded-glass-sm border ${w.bg}`}>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${w.color}`}>
                        {w.label}
                      </span>
                      <span className={`${w.color} text-sm`}>{w.msg}</span>
                    </div>
                  </div>
                );
              })()}
              
              {/* Waste Type Breakdown Table with Reliability */}
              <div className="glass-card overflow-hidden mb-6">
                <h3 className="font-semibold text-text-primary p-4 border-b border-glass-border">Per Waste Type Accuracy (Real-World)</h3>
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-glass-border bg-glass-white/50">
                      <th className="text-left p-4 text-sm font-medium text-text-secondary">Waste Type</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">Predicted (kg)</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">Actual (kg)</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">Error (kg)</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">MAE (kg)</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">RMSE (kg)</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">R²</th>
                      <th className="text-right p-4 text-sm font-medium text-text-secondary">Accuracy</th>
                      <th className="text-center p-4 text-sm font-medium text-text-secondary">Samples</th>
                      <th className="text-center p-4 text-sm font-medium text-text-secondary">Reliability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(realWorldMetrics.by_waste_type || {}).map(([wt, data]) => {
                      const displayNames = {
                        'wet': 'Wet Waste',
                        'dry': 'Dry Waste',
                        'plastic': 'Plastic Waste',
                        'glass': 'Glass Waste',
                        'metal': 'Metal Waste',
                        'medical': 'Medical Waste',
                        'total': 'Total Waste'
                      }
                      const error = data.available 
                        ? Math.abs((data.total_predicted_kg || 0) - (data.total_actual_kg || 0))
                        : 0
                      
                      const reliability = data.reliability || (data.sample_count < 6 ? { level: "INSUFFICIENT_DATA", label: "Insufficient Data", color: "text-red-400", bg_color: "bg-red-500/10" } :
                                                                data.sample_count < 21 ? { level: "EARLY_EVALUATION", label: "Early Evaluation", color: "text-yellow-400", bg_color: "bg-yellow-500/10" } :
                                                                data.sample_count < 51 ? { level: "MODERATE_CONFIDENCE", label: "Moderate Confidence", color: "text-blue-400", bg_color: "bg-blue-500/10" } :
                                                                { level: "STRONG_EVALUATION", label: "Strong Evaluation", color: "text-emerald-400", bg_color: "bg-emerald-500/10" });
                      
                      return (
                        <tr key={wt} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                          <td className="p-4 font-medium text-text-primary">{displayNames[wt] || wt}</td>
                          <td className="p-4 text-right text-text-primary">
                            {data.available ? (data.total_predicted_kg?.toFixed(1) || 0) : 'N/A'}
                          </td>
                          <td className="p-4 text-right text-text-primary">
                            {data.available ? (data.total_actual_kg?.toFixed(1) || 0) : 'N/A'}
                          </td>
                          <td className="p-4 text-right">
                            {data.available 
                              ? <span className={getErrorColor(error)}>{error.toFixed(1)}</span>
                              : <span className="text-text-muted">N/A</span>
                            }
                          </td>
                          <td className="p-4 text-right">
                            {data.available && data.mae_kg !== undefined 
                              ? <span className={getErrorColor(data.mae_kg)}>{formatMetric(data.mae_kg)}</span>
                              : <span className="text-text-muted">N/A</span>
                            }
                          </td>
                          <td className="p-4 text-right">
                            {data.available && data.rmse_kg !== undefined 
                              ? <span className={getErrorColor(data.rmse_kg)}>{formatMetric(data.rmse_kg)}</span>
                              : <span className="text-text-muted">N/A</span>
                            }
                          </td>
                          <td className="p-4 text-right">
                            {data.available && data.r2 !== "N/A" && data.r2 !== undefined 
                              ? <span className={getMetricColor(data.r2)}>{formatMetric(data.r2)}</span>
                              : <span className="text-text-muted">N/A — insufficient data</span>
                            }
                          </td>
                          <td className="p-4 text-right">
                            {data.available && data.r2 !== "N/A" && data.r2 !== undefined 
                              ? <span className={getMetricColor(data.r2)}>{formatAccuracy(data.r2)}</span>
                              : <span className="text-text-muted">N/A — insufficient data</span>
                            }
                          </td>
                          <td className="p-4 text-center text-text-secondary">
                            {data.available ? formatCount(data.sample_count) : '0'}
                          </td>
                          <td className="p-4 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${reliability.bg_color} ${reliability.color}`}>
                              {reliability.label}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              
              {/* Prediction vs Actual Chart */}
              <div className="glass-card">
                <div className="p-4 border-b border-glass-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <h3 className="font-semibold text-text-primary">Prediction vs Actual</h3>
                  <div className="flex gap-2">
                    {(['total', 'wet', 'dry', 'plastic', 'glass', 'metal', 'medical']).map(wt => (
                      <button
                        key={wt}
                        onClick={() => setSelectedWasteType(wt)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                          selectedWasteType === wt 
                            ? 'bg-emerald-500 text-black' 
                            : 'bg-glass-white/10 text-text-secondary hover:bg-glass-white/20'
                        }`}
                      >
                        {wt.charAt(0).toUpperCase() + wt.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="p-4">
                  {loadingChart ? (
                    <div className="h-80 flex items-center justify-center">
                      <LoadingState text="Loading chart data..." />
                    </div>
                  ) : (!chartData || !chartData.available || !chartData.data || chartData.data.length === 0) ? (
                    <div className="h-80 flex items-center justify-center text-text-muted">
                      <p>Insufficient real-world data for meaningful comparison.</p>
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={chartData.data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis 
                          dataKey="date" 
                          stroke="#666" 
                          fontSize={11} 
                          tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        />
                        <YAxis stroke="#666" fontSize={11} />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1e1e1e', 
                            border: '1px solid #333',
                            borderRadius: '8px'
                          }}
                          formatter={(value, name) => [
                            value,
                            name === 'predicted' ? 'Predicted (kg)' : name === 'actual' ? 'Actual (kg)' : 'Error (kg)'
                          ]}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="predicted" 
                          stroke="#00d46a" 
                          strokeWidth={2} 
                          dot={{ fill: '#00d46a', strokeWidth: 2, r: 4 }}
                          name="Predicted"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="actual" 
                          stroke="#3b82f6" 
                          strokeWidth={2} 
                          dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                          name="Actual"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="error" 
                          stroke="#ef4444" 
                          strokeWidth={1.5} 
                          strokeDasharray="5 5"
                          dot={{ fill: '#ef4444', strokeWidth: 2, r: 3 }}
                          name="Error"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* ===== SECTION 8: ML MODEL HEALTH & MONITORING ===== */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">ML Model Health & Monitoring</h2>
          
          {/* A. Overall Model Health */}
          {(loadingHealth || loadingDrift || loadingPerfTrend) ? (
            <GlassCard className="p-6 text-center">
              <LoadingState text="Loading ML monitoring data..." />
            </GlassCard>
          ) : mlHealth && (
            <>
              <GlassCard className={`p-6 mb-6 border-l-4 ${getHealthStatusColor(mlHealth.health_status).replace('text-', 'border-')}`}>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                  <h3 className="font-semibold text-text-primary">Overall Model Health</h3>
                  <span className={`px-4 py-2 rounded-full text-lg font-bold ${getHealthStatusColor(mlHealth.health_status)}`}>
                    {mlHealth.health_status}
                  </span>
                </div>
                <div className="text-text-secondary mb-4">{mlHealth.health_reason}</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Overall Drift</div>
                    <div className="font-bold text-text-primary capitalize">{mlHealth.overall_drift_status?.replace(/_/g, ' ') || 'N/A'}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Real-World Samples</div>
                    <div className="font-bold text-text-primary">{formatCount(mlHealth.total_real_world_samples)}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Reliability</div>
                    <div className="font-bold text-text-primary">{mlHealth.reliability?.label || 'N/A'}</div>
                  </div>
                  <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                    <div className="text-text-secondary text-xs mb-1">Degradation</div>
                    <div className="font-bold text-text-primary">
                      {mlHealth.performance_degradation_summary?.significant_degradation_count || 0} Critical, 
                      {mlHealth.performance_degradation_summary?.noticeable_degradation_count || 0} Warning
                    </div>
                  </div>
                </div>
              </GlassCard>

              {/* B. Data Drift Table */}
              {dataDrift && dataDrift.available && (
                <GlassCard className="p-6 mb-6">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                    <h3 className="font-semibold text-text-primary">Data Drift Detection</h3>
                    <div className="flex flex-wrap gap-2 text-sm">
                      <span className="px-2 py-1 bg-glass-white/10 rounded-glass-sm">
                        Reference: <span className="font-mono">{dataDrift.reference_source || 'unknown'}</span>
                      </span>
                      <span className="px-2 py-1 bg-glass-white/10 rounded-glass-sm">
                        Model: <span className="font-mono">{dataDrift.reference_model_version || 'unknown'}</span>
                      </span>
                      <span className="px-2 py-1 bg-glass-white/10 rounded-glass-sm">
                        Ref Period: <span className="font-mono">{dataDrift.reference_period_days}d</span>
                      </span>
                      <span className="px-2 py-1 bg-glass-white/10 rounded-glass-sm">
                        Recent: <span className="font-mono">{dataDrift.recent_period_days}d</span>
                      </span>
                    </div>
                  </div>
                  <div className="glass-card overflow-hidden">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-glass-border bg-glass-white/50">
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Feature</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">Type</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Ref Samples</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Recent Samples</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">PSI</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Mean Δ%</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Std Δ%</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">KS p-value</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">χ² p-value</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Cramér's V</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(dataDrift.features || {}).map(([feature, data]) => {
                          const displayNames = {
                            'wet': 'Wet Waste',
                            'dry': 'Dry Waste',
                            'plastic': 'Plastic Waste',
                            'glass': 'Glass Waste',
                            'metal': 'Metal Waste',
                            'medical': 'Medical Waste',
                            'total': 'Total Waste',
                            'submission_frequency': 'Submission Frequency',
                            'area': 'Area Distribution',
                            'account_type': 'Account Type Distribution'
                          }
                          const isCategorical = data.feature_type === 'categorical'
                          return (
                            <tr key={feature} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                              <td className="p-4 font-medium text-text-primary">{displayNames[feature] || feature}</td>
                              <td className="p-4 text-center text-text-secondary text-sm">
                                {isCategorical ? 'Categorical' : 'Numerical'}
                              </td>
                              <td className="p-4 text-right text-text-secondary">{formatCount(data.reference_samples)}</td>
                              <td className="p-4 text-right text-text-secondary">{formatCount(data.recent_samples)}</td>
                              <td className="p-4 text-right text-text-secondary">
                                {!isCategorical && data.psi !== null && data.psi !== undefined ? data.psi.toFixed(4) : 'N/A'}
                              </td>
                              <td className="p-4 text-right text-text-secondary">
                                {!isCategorical && data.mean_change_pct !== null && data.mean_change_pct !== undefined ? data.mean_change_pct.toFixed(1) + '%' : 'N/A'}
                              </td>
                              <td className="p-4 text-right text-text-secondary">
                                {!isCategorical && data.std_change_pct !== null && data.std_change_pct !== undefined ? data.std_change_pct.toFixed(1) + '%' : 'N/A'}
                              </td>
                              <td className="p-4 text-right text-text-secondary">
                                {!isCategorical && data.ks_pvalue !== null && data.ks_pvalue !== undefined ? data.ks_pvalue.toFixed(6) : 'N/A'}
                              </td>
                              <td className="p-4 text-right text-text-secondary">
                                {isCategorical && data.chi2_pvalue !== null && data.chi2_pvalue !== undefined ? data.chi2_pvalue.toFixed(6) : 'N/A'}
                              </td>
                              <td className="p-4 text-right text-text-secondary">
                                {isCategorical && data.cramers_v !== null && data.cramers_v !== undefined ? data.cramers_v.toFixed(4) : 'N/A'}
                              </td>
                              <td className="p-4 text-center">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getDriftStatusColor(data.status)}`}>
                                  {getDriftStatusLabel(data.status)}
                                </span>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                  {dataDrift.summary && (
                    <div className="mt-4 p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border text-sm text-text-secondary">
                      Summary: {dataDrift.summary.high_drift} High, {dataDrift.summary.moderate_drift} Moderate, {dataDrift.summary.no_drift} No Drift, {dataDrift.summary.insufficient_data} Insufficient Data
                    </div>
                  )}
                </GlassCard>
              )}

              {/* C. Performance Trend */}
              {performanceTrend && performanceTrend.available && (
                <GlassCard className="p-6 mb-6">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                    <h3 className="font-semibold text-text-primary">Real-World Performance Trend</h3>
                    <p className="text-sm text-text-secondary">{performanceTrend.real_world_note}</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-glass-border bg-glass-white/50">
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Period</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">Waste Type</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline R²</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World R²</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline MAE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World MAE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline RMSE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World RMSE</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">Samples</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(performanceTrend.periods || {}).map(([periodKey, periodData]) => {
                          const periodLabel = periodKey === 'overall' ? 'All Time' : periodKey.replace('last_', 'Last ').replace('_days', ' Days')
                          const offline = periodData.offline_test || {}
                          const realWorld = periodData.real_world || {}
                          return Object.entries(realWorld).map(([wt, rw]) => {
                            const off = offline[wt] || {}
                            const displayNames = {
                              'wet': 'Wet', 'dry': 'Dry', 'plastic': 'Plastic', 'glass': 'Glass', 'metal': 'Metal', 'medical': 'Medical', 'total': 'Total'
                            }
                            if (!rw.available) return null
                            const degradation = rw.reliability ? 
                              (off.R2 && rw.R2 !== undefined && off.R2 > 0 ? 
                                (off.R2 - rw.R2) / off.R2 * 100 : null) : null
                            let status = 'STABLE'
                            let statusLabel = 'Stable'
                            if (degradation !== null) {
                              if (degradation >= 25) { status = 'SIGNIFICANT_DEGRADATION'; statusLabel = 'Significant Degradation' }
                              else if (degradation >= 10) { status = 'NOTICEABLE_DEGRADATION'; statusLabel = 'Noticeable Degradation' }
                              else { status = 'STABLE'; statusLabel = 'Stable' }
                            } else {
                              status = 'INSUFFICIENT_DATA'; statusLabel = 'Insufficient Data'
                            }
                            return (
                              <tr key={`${periodKey}-${wt}`} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                                <td className="p-4 font-medium text-text-primary">{periodLabel}</td>
                                <td className="p-4 text-center text-text-primary">{displayNames[wt] || wt}</td>
                                <td className="p-4 text-right text-text-secondary">{typeof off.R2 === 'number' ? off.R2.toFixed(4) : 'N/A'}</td>
                                <td className="p-4 text-right">{typeof rw.R2 === 'number' ? <span className={getMetricColor(rw.R2)}>{rw.R2.toFixed(4)}</span> : 'N/A'}</td>
                                <td className="p-4 text-right text-text-secondary">{typeof off.MAE === 'number' ? off.MAE.toFixed(4) : 'N/A'}</td>
                                <td className="p-4 text-right">{typeof rw.MAE === 'number' ? <span className={getErrorColor(rw.MAE)}>{rw.MAE.toFixed(4)}</span> : 'N/A'}</td>
                                <td className="p-4 text-right text-text-secondary">{typeof off.RMSE === 'number' ? off.RMSE.toFixed(4) : 'N/A'}</td>
                                <td className="p-4 text-right">{typeof rw.RMSE === 'number' ? <span className={getErrorColor(rw.RMSE)}>{rw.RMSE.toFixed(4)}</span> : 'N/A'}</td>
                                <td className="p-4 text-center text-text-secondary">{formatCount(rw.sample_count)}</td>
                                <td className="p-4 text-center">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDegradationColor(status)}`}>
                                    {statusLabel}
                                  </span>
                                </td>
                              </tr>
                            )
                          })
                        })}
                      </tbody>
                    </table>
                  </div>
                </GlassCard>
              )}

              {/* D. Prediction Accuracy Trend */}
              {performanceTrend && performanceTrend.available && (
                <GlassCard className="p-6 mb-6">
                  <h3 className="font-semibold text-text-primary mb-4">Prediction Accuracy Trend (Real-World R²)</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {(['total', 'wet', 'dry', 'plastic', 'glass', 'metal', 'medical']).map(wt => {
                      const displayNames = {
                        'wet': 'Wet', 'dry': 'Dry', 'plastic': 'Plastic', 'glass': 'Glass', 'metal': 'Metal', 'medical': 'Medical', 'total': 'Total'
                      }
                      const r2Values = []
                      const periods = ['last_7_days', 'last_30_days', 'last_90_days', 'overall']
                      periods.forEach(p => {
                        const rw = performanceTrend.periods?.[p]?.real_world?.[wt]
                        if (rw?.available && typeof rw.R2 === 'number') {
                          r2Values.push({ period: p, r2: rw.R2 })
                        }
                      })
                      if (r2Values.length < 2) {
                        return (
                          <div key={wt} className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border text-center">
                            <div className="font-medium text-text-primary">{displayNames[wt]}</div>
                            <div className="text-text-muted text-sm mt-1">Insufficient trend data</div>
                          </div>
                        )
                      }
                      const trend = r2Values[r2Values.length - 1].r2 - r2Values[0].r2
                      let trendLabel = 'Stable'
                      let trendColor = 'text-emerald-400'
                      if (trend < -0.05) { trendLabel = 'Worsening'; trendColor = 'text-red-400' }
                      else if (trend > 0.05) { trendLabel = 'Improving'; trendColor = 'text-emerald-400' }
                      return (
                        <div key={wt} className="p-4 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                          <div className="font-medium text-text-primary">{displayNames[wt]}</div>
                          <div className={`text-2xl font-bold ${getMetricColor(r2Values[r2Values.length - 1].r2)} mt-1`}>
                            {r2Values[r2Values.length - 1].r2.toFixed(4)}
                          </div>
                          <div className={`text-sm ${trendColor} mt-1`}>{trendLabel} ({trend >= 0 ? '+' : ''}{trend.toFixed(4)})</div>
                          <div className="text-xs text-text-muted mt-2">
                            {r2Values.map(v => `${v.period.replace('last_', '').replace('_days', 'd')}: ${v.r2.toFixed(3)}`).join(' | ')}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </GlassCard>
              )}

{/* E. Model Warning Panel */}
              {mlHealth && (
                <GlassCard className="p-6 mb-6 border-l-4 border-yellow-400">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                    <h3 className="font-semibold text-text-primary">Model Warning Panel</h3>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthStatusColor(mlHealth.health_status)}`}>
                        {getHealthStatusLabel(mlHealth.health_status)}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getReliabilityColor(mlHealth.reliability_level)}`}>
                        {getReliabilityLabel(mlHealth.reliability_level)}
                      </span>
                    </div>
                  </div>
                  <div className="text-text-secondary mb-4">{mlHealth.health_reason}</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                      <div className="text-text-secondary text-xs mb-1">Overall Drift</div>
                      <div className="font-bold text-text-primary">{getDriftStatusLabel(mlHealth.overall_drift_status)}</div>
                    </div>
                    <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                      <div className="text-text-secondary text-xs mb-1">Real-World Samples</div>
                      <div className="font-bold text-text-primary">{formatCount(mlHealth.total_real_world_samples)}</div>
                    </div>
                    <div className="p-3 bg-glass-white/50 rounded-glass-sm border border-glass-border">
                      <div className="text-text-secondary text-xs mb-1">Coverage</div>
                      <div className="font-bold text-text-primary">{mlHealth.prediction_coverage?.coverage?.coverage_pct || 0}%</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {mlHealth.health_status === 'INSUFFICIENT_DATA' && (
                      <div className="p-3 bg-gray-500/10 border border-gray-500/30 rounded-glass-sm">
                        <span className="text-yellow-400 font-medium">⚠️ Insufficient Data:</span> {mlHealth.health_reason}
                      </div>
                    )}
                    {mlHealth.overall_drift_status === 'HIGH_DRIFT' && (
                      <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm">
                        <span className="text-red-400 font-medium">🔴 High Data Drift:</span> Incoming waste data distribution has significantly shifted from training reference. Investigate recent waste patterns.
                      </div>
                    )}
                    {mlHealth.overall_drift_status === 'MODERATE_DRIFT' && (
                      <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm">
                        <span className="text-yellow-400 font-medium">🟡 Moderate Data Drift:</span> Some feature distributions have shifted. Monitor closely.
                      </div>
                    )}
                    {mlHealth.performance_degradation_summary?.significant_degradation > 0 && (
                      <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-glass-sm">
                        <span className="text-red-400 font-medium">🔴 Significant Degradation:</span> {mlHealth.performance_degradation_summary.significant_degradation} waste type(s) show significant accuracy degradation vs offline test.
                      </div>
                    )}
                    {mlHealth.performance_degradation_summary?.noticeable_degradation > 0 && (
                      <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-glass-sm">
                        <span className="text-yellow-400 font-medium">🟡 Noticeable Degradation:</span> {mlHealth.performance_degradation_summary.noticeable_degradation} waste type(s) show noticeable accuracy degradation.
                      </div>
                    )}
                    {dataDrift && dataDrift.features && Object.entries(dataDrift.features).map(([f, d]) => {
                      if (d.status === 'MODERATE_DRIFT' || d.status === 'HIGH_DRIFT') {
                        const isCategorical = d.feature_type === 'categorical'
                        return (
                          <div key={f} className={`p-3 rounded-glass-sm border ${d.status === 'HIGH_DRIFT' ? 'bg-red-500/10 border-red-500/30' : 'bg-yellow-500/10 border-yellow-500/30'}`}>
                            <span className={`font-medium ${d.status === 'HIGH_DRIFT' ? 'text-red-400' : 'text-yellow-400'}`}>
                              {d.status === 'HIGH_DRIFT' ? '🔴 High' : '🟡 Moderate'} drift in {f.replace(/_/g, ' ')} ({isCategorical ? 'Categorical' : 'Numerical'})
                            </span>:
                            {!isCategorical && d.psi !== undefined ? ` PSI=${d.psi.toFixed(4)}, Mean Δ=${d.mean_change_pct?.toFixed(1)}%` : ''}
                            {isCategorical && d.chi2_pvalue !== undefined ? ` χ² p=${d.chi2_pvalue.toFixed(6)}, V=${d.cramers_v?.toFixed(4)}` : ''}
                          </div>
                        )
                      }
                      return null
                    })}
                    {mlHealth.health_status === 'HEALTHY' && (
                      <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-glass-sm">
                        <span className="text-emerald-400 font-medium">🟢 Healthy:</span> No data drift and stable prediction accuracy. Continue regular monitoring.
                      </div>
                    )}
                    {mlHealth.health_status !== 'HEALTHY' && 
                      mlHealth.health_status !== 'INSUFFICIENT_DATA' && 
                      mlHealth.health_status !== 'WARNING' && 
                      mlHealth.health_status !== 'CRITICAL' && 
                      mlHealth.overall_drift_status !== 'HIGH_DRIFT' && 
                      mlHealth.overall_drift_status !== 'MODERATE_DRIFT' && 
                      mlHealth.performance_degradation_summary?.significant_degradation === 0 && 
                      mlHealth.performance_degradation_summary?.noticeable_degradation === 0 && (
                      <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-glass-sm">
                        <span className="text-blue-400 font-medium">🔵 Monitoring Active:</span> No critical issues detected. Continue regular checks.
                      </div>
                    )}
                  </div>
                </GlassCard>
              )}

              {/* F. Model Comparison */}
              {modelComparison && modelComparison.models && (
                <GlassCard className="p-6 mb-6">
                  <h3 className="font-semibold text-text-primary mb-4">Model Comparison</h3>
                  <p className="text-sm text-text-secondary mb-2">{modelComparison.note}</p>
                  <p className="text-sm text-text-secondary mb-4">{modelComparison.offline_test_note}</p>
                  <p className="text-sm text-text-secondary mb-4">{modelComparison.real_world_note}</p>
                  <div className="glass-card overflow-hidden">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-glass-border bg-glass-white/50">
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Model</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline R²</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline MAE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline RMSE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Offline SMAPE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World R²</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World MAE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World RMSE</th>
                          <th className="text-right p-4 text-sm font-medium text-text-secondary">Real-World SMAPE</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">RW Samples</th>
                          <th className="text-center p-4 text-sm font-medium text-text-secondary">RW Reliability</th>
                          <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(modelComparison.models).map(([modelId, model]) => (
                          <tr key={modelId} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                            <td className="p-4 font-medium text-text-primary">{model.name}</td>
                            <td className="p-4 text-right text-text-secondary">{typeof model.offline_R2 === 'number' ? model.offline_R2.toFixed(4) : 'N/A'}</td>
                            <td className="p-4 text-right text-text-secondary">{typeof model.offline_MAE === 'number' ? model.offline_MAE.toFixed(4) : 'N/A'}</td>
                            <td className="p-4 text-right text-text-secondary">{typeof model.offline_RMSE === 'number' ? model.offline_RMSE.toFixed(4) : 'N/A'}</td>
                            <td className="p-4 text-right text-text-secondary">{typeof model.offline_SMAPE === 'number' ? model.offline_SMAPE.toFixed(2) + '%' : 'N/A'}</td>
                            <td className="p-4 text-right">
                              {typeof model.real_world_R2 === 'number' 
                                ? <span className={getMetricColor(model.real_world_R2)}>{model.real_world_R2.toFixed(4)}</span> 
                                : 'N/A'}
                            </td>
                            <td className="p-4 text-right">
                              {typeof model.real_world_MAE === 'number' 
                                ? <span className={getErrorColor(model.real_world_MAE)}>{model.real_world_MAE.toFixed(4)}</span> 
                                : 'N/A'}
                            </td>
                            <td className="p-4 text-right">
                              {typeof model.real_world_RMSE === 'number' 
                                ? <span className={getErrorColor(model.real_world_RMSE)}>{model.real_world_RMSE.toFixed(4)}</span> 
                                : 'N/A'}
                            </td>
                            <td className="p-4 text-right">
                              {typeof model.real_world_SMAPE === 'number' 
                                ? <span className={getErrorColor(model.real_world_SMAPE)}>{model.real_world_SMAPE.toFixed(2)}%</span> 
                                : 'N/A'}
                            </td>
                            <td className="p-4 text-center text-text-secondary">{formatCount(model.real_world_samples || 0)}</td>
                            <td className="p-4 text-center">
                              {model.real_world_reliability ? (
                                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getReliabilityColor(model.real_world_reliability.level)}`}>
                                  {getReliabilityLabel(model.real_world_reliability.level)}
                                </span>
                              ) : 'N/A'}
                            </td>
                            <td className="p-4 text-left text-text-secondary">{model.status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </GlassCard>
              )}

              {/* G. Recommendations */}
              {mlHealth && dataDrift && performanceTrend && (
                <GlassCard className="p-6 mb-6 border-l-4 border-emerald-400">
                  <h3 className="font-semibold text-text-primary mb-3">Recommendations</h3>
                  <div className="space-y-2">
                    {mlHealth.recommendations?.map((rec, idx) => (
                      <div key={idx} className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-glass-sm flex items-start gap-3">
                        <span className="text-emerald-400 mt-0.5">•</span>
                        <span className="text-text-secondary text-sm">{rec}</span>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}