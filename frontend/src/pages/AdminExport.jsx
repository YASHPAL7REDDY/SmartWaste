import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  GlassInput, 
  Navbar, 
  LoadingState 
} from '../components'

export function AdminExport() {
  const { isAuthenticated, role } = useAuth()
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - 30)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0])
  const [format, setFormat] = useState('csv')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  if (!isAuthenticated || role !== 'admin') {
    return <Navigate to="/" replace />
  }

  const handleExport = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    
    if (!startDate || !endDate) {
      setError('Please select both start and end dates')
      return
    }
    
    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date')
      return
    }
    
    setLoading(true)
    
    try {
      const response = await api.get('/admin/export', {
        params: { start_date: startDate, end_date: endDate, format },
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `smartwaste_export_${startDate}_to_${endDate}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      setSuccess('Export completed successfully!')
    } catch (err) {
      setError(err.response?.data?.detail || 'Export failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  const formatOptions = [
    { value: 'csv', label: 'CSV' },
    { value: 'excel', label: 'Excel' }
  ]
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-2xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Export Data</h1>
          <p className="text-text-secondary mt-1">Download waste submission data for analysis</p>
        </div>
        
        {error && (
          <div className="inline-error mb-6" role="alert">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        
        {success && (
          <div className="inline-error mb-6 bg-green-500/10 border-green-500/20 text-green-400" role="alert">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{success}</span>
          </div>
        )}
        
        <GlassCard>
          <form onSubmit={handleExport} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <GlassInput
                label="Start Date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
              <GlassInput
                label="End Date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
            
            <GlassInput
              label="Format"
              type="select"
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              options={formatOptions}
            />
            
            <div className="bg-glass-white/50 rounded-glass-sm p-4">
              <h4 className="font-medium text-text-primary mb-2">Export Details</h4>
              <ul className="space-y-1 text-sm text-text-secondary">
                <li>• Includes individual waste categories: Wet, Dry, Plastic, Glass, Metal, Medical</li>
                <li>• Includes totals and collection status</li>
                <li>• Date range inclusive (start and end dates included)</li>
                <li>• Data sourced from real database submissions only</li>
              </ul>
            </div>
            
            <GlassButton variant="primary" type="submit" className="w-full" loading={loading}>
              EXPORT DATA
            </GlassButton>
          </form>
        </GlassCard>
      </div>
    </div>
  )
}

import { Navigate } from 'react-router-dom'