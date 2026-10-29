import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  Navbar, 
  LoadingState, 
  EmptyState,
  GlassButton
} from '../components'
import { format } from 'date-fns'

// Safe date formatting helper
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return 'N/A'
  try {
    return format(date, 'MMM d, yyyy')
  } catch {
    return 'N/A'
  }
}

// Safe number formatting helper
const formatNumber = (num, decimals = 2) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  try {
    return Number(num).toFixed(decimals)
  } catch {
    return 'N/A'
  }
}

// Case-insensitive status check
const isCollected = (status) => {
  if (!status) return false
  return String(status).toLowerCase() === 'collected'
}

export function MySubmissions() {
  const { user } = useAuth()
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const limit = 10
  
  useEffect(() => {
    fetchSubmissions()
  }, [page])
  
  const fetchSubmissions = async () => {
    try {
      setLoading(true)
      const response = await api.get('/waste/my-submissions', { 
        params: { limit, offset: page * limit } 
      })
      
      if (page === 0) {
        setSubmissions(response.data)
      } else {
        setSubmissions(prev => [...prev, ...response.data])
      }
      
      setHasMore(response.data.length === limit)
    } catch (err) {
      setError('Failed to load submissions')
    } finally {
      setLoading(false)
    }
  }
  
  const loadMore = () => {
    setPage(prev => prev + 1)
  }
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">My Submissions</h1>
          <p className="text-text-secondary mt-1">View your waste submission history</p>
        </div>
        
        {error && (
          <div className="inline-error mb-6" role="alert">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        
        {loading && submissions.length === 0 ? (
          <LoadingState text="Loading submissions..." />
        ) : submissions.length === 0 ? (
          <EmptyState
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            title="No Submissions Yet"
            description="Start by submitting your waste data from the Collect page"
            action={{ label: 'Collect Data', onClick: () => navigate('/collect') }}
          />
        ) : (
          <>
            <div className="glass-card overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Date</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Waste Breakdown</th>
                    <th className="text-right p-4 text-sm font-medium text-text-secondary">Total (kg)</th>
                    <th className="text-left p-4 text-sm font-medium text-text-secondary">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((sub) => (
                    <tr key={sub.id} className="border-b border-glass-border/50 hover:bg-glass-white-strong/50">
                      <td className="p-4 text-text-primary">{formatDate(sub.submission_date)}</td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {sub.items_count > 0 && (
                            <span className="px-2 py-0.5 rounded text-xs bg-glass-white-strong border border-glass-border text-text-secondary">
                              {sub.items_count} types
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-right font-medium text-text-primary">{formatNumber(sub.total_waste_kg)}</td>
                      <td className="p-4">
                        <span className={`
                          px-2 py-1 rounded-full text-xs font-medium
                          ${isCollected(sub.collection_status) ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}
                        `}>
                          {sub.collection_status || 'UNKNOWN'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {hasMore && (
              <div className="text-center mt-6">
                <GlassButton variant="default" onClick={loadMore} loading={loading}>
                  Load More
                </GlassButton>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}