import { Link } from 'react-router-dom'
import { useLocation } from 'react-router-dom'
import { GlassButton, GlassCard } from '../components'

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

export function SubmitSuccess() {
  const location = useLocation()
  const submission = location.state?.submission
  
  return (
    <div className="page-container flex min-h-screen items-center justify-center py-20">
      <div className="max-w-md w-full px-6 animate-in">
        <GlassCard padding="p-10">
          <div className="w-20 h-20 rounded-full bg-emerald/10 border border-emerald/30 flex items-center justify-center mx-auto mb-8 animate-pulse-glow">
            <svg className="w-10 h-10 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-text-primary mb-2">Waste Submitted Successfully</h1>
          
          {submission && (
            <div className="bg-glass-white/50 rounded-glass-sm p-4 mb-6 text-left">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Submission ID</span>
                  <span className="font-mono text-text-primary">{submission.id.slice(0, 12)}...</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Date</span>
                  <span className="font-medium text-text-primary">{formatDate(submission.submission_date)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Total Waste</span>
                  <span className="font-bold text-emerald">{submission.total_waste_kg} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Status</span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400">
                    {submission.collection_status}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <p className="text-text-secondary mb-8">
            Your waste data has been recorded. ML predictions will be generated automatically.
          </p>
          
          <div className="flex flex-col gap-3">
            <Link to="/dashboard">
              <GlassButton variant="primary" className="w-full">
                Back to Dashboard
              </GlassButton>
            </Link>
            <Link to="/collect">
              <GlassButton variant="default" className="w-full">
                Submit More Waste
              </GlassButton>
            </Link>
            <Link to="/predictions">
              <GlassButton variant="ghost" className="w-full">
                View Predictions
              </GlassButton>
            </Link>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}

import { format } from 'date-fns'