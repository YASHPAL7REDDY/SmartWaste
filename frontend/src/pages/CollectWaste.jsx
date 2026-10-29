import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { 
  GlassCard, 
  GlassButton, 
  GlassInput, 
  Navbar, 
  LoadingState 
} from '../components'

const WASTE_TYPES = [
  { key: 'wet', label: 'Wet', icon: '💧', color: 'blue' },
  { key: 'dry', label: 'Dry', icon: '📦', color: 'gray' },
  { key: 'plastic', label: 'Plastic', icon: '🥤', color: 'yellow' },
  { key: 'glass', label: 'Glass', icon: '🍾', color: 'green' },
  { key: 'metal', label: 'Metal', icon: '♻️', color: 'orange' },
  { key: 'medical', label: 'Medical', icon: '🏥', color: 'red' },
]

export function CollectWaste() {
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [selectedTypes, setSelectedTypes] = useState({})
  const [quantities, setQuantities] = useState({})
  const [peoplePresent, setPeoplePresent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [submissionData, setSubmissionData] = useState(null)
  const [showVerify, setShowVerify] = useState(false)
  
  // Initialize selected types and quantities
  useEffect(() => {
    const initialSelected = {}
    const initialQuantities = {}
    WASTE_TYPES.forEach(t => {
      initialSelected[t.key] = false
      initialQuantities[t.key] = ''
    })
    setSelectedTypes(initialSelected)
    setQuantities(initialQuantities)
  }, [])
  
  // Load user profile for defaults
  useEffect(() => {
    if (user) {
      setPeoplePresent(
        user.account_type === 'family' ? user.family_members || '' :
        user.account_type === 'restaurant' ? user.avg_customers_per_day || '' :
        user.employee_count || ''
      )
    }
  }, [user])
  
  const toggleType = (type) => {
    setSelectedTypes(prev => ({ ...prev, [type]: !prev[type] }))
    if (!selectedTypes[type]) {
      setQuantities(prev => ({ ...prev, [type]: '' }))
    }
  }
  
  const updateQuantity = (type, value) => {
    setQuantities(prev => ({ ...prev, [type]: value }))
  }
  
  const validateForm = () => {
    const selected = Object.keys(selectedTypes).filter(k => selectedTypes[k])
    if (selected.length === 0) {
      setError('Please select at least one waste type')
      return false
    }
    
    for (const type of selected) {
      const qty = parseFloat(quantities[type])
      if (isNaN(qty) || qty < 0) {
        setError(`Please enter a valid quantity for ${type}`)
        return false
      }
    }
    
    if (peoplePresent !== '' && (isNaN(parseInt(peoplePresent)) || parseInt(peoplePresent) < 0)) {
      setError('Please enter a valid number for people present')
      return false
    }
    
    return true
  }
  
  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    
    if (!validateForm()) return
    
    // Prepare verification data
    const items = WASTE_TYPES
      .filter(t => selectedTypes[t.key])
      .map(t => ({
        waste_type: t.key,
        quantity_kg: parseFloat(quantities[t.key])
      }))
    
    const totalWaste = items.reduce((sum, item) => sum + item.quantity_kg, 0)
    
    const verificationData = {
      submission_date: new Date().toISOString().split('T')[0],
      submission_time: new Date().toTimeString().slice(0, 5),
      day_type: new Date().getDay() >= 5 ? 'weekend' : 'normal_day',
      people_present: peoplePresent ? parseInt(peoplePresent) : null,
      items,
      area: user?.area,
      account_type: user?.account_type,
      family_members: user?.family_members,
      customers: user?.avg_customers_per_day,
      total_waste_kg: totalWaste,
    }
    
    setSubmissionData(verificationData)
    setShowVerify(true)
  }
  
  const handleVerifySubmit = async () => {
    if (!submissionData) return
    
    setLoading(true)
    setError('')
    
    try {
      const response = await api.post('/waste/submit', submissionData)
      navigate('/submit-success', { state: { submission: response.data } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed. Please try again.')
      setShowVerify(false)
    } finally {
      setLoading(false)
    }
  }
  
  const handleEdit = () => {
    setShowVerify(false)
  }
  
  // Main form
  if (!showVerify) {
    return (
      <div className="page-container pt-20">
        <Navbar />
        <div className="section-container max-w-4xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-text-primary">Collect Waste Data</h1>
            <p className="text-text-secondary mt-1">Record your separated waste submission</p>
          </div>
          
          {error && (
            <div className="inline-error mb-6" role="alert">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{error}</span>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Waste Type Selection */}
            <GlassCard>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Select Waste Types</h3>
              <p className="text-text-secondary text-sm mb-6">Choose all categories you're submitting today</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {WASTE_TYPES.map((type) => (
                  <button
                    key={type.key}
                    type="button"
                    onClick={() => toggleType(type.key)}
                    className={`
                      relative p-4 rounded-glass border transition-all duration-fast text-left
                      ${selectedTypes[type.key] 
                        ? 'border-emerald/50 bg-emerald/5' 
                        : 'border-glass-border bg-glass-white hover:border-emerald/30 hover:bg-emerald/5'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{type.icon}</span>
                      <span className="font-medium text-text-primary">{type.label}</span>
                    </div>
                    {selectedTypes[type.key] && (
                      <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-emerald flex items-center justify-center">
                        <svg className="w-3 h-3 text-matte-black" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </GlassCard>
            
            {/* Quantities */}
            {Object.keys(selectedTypes).some(k => selectedTypes[k]) && (
              <GlassCard>
                <h3 className="text-lg font-semibold text-text-primary mb-4">Enter Quantities (kg)</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {WASTE_TYPES
                    .filter(t => selectedTypes[t.key])
                    .map((type) => (
                      <GlassInput
                        key={type.key}
                        label={`${type.label} Waste`}
                        type="number"
                        step="0.1"
                        min="0"
                        value={quantities[type.key]}
                        onChange={(e) => updateQuantity(type.key, e.target.value)}
                        placeholder="0.0"
                        required
                      />
                    ))}
                </div>
                
                <div className="mt-6 pt-4 border-t border-glass-border">
                  <div className="flex justify-between items-center text-lg">
                    <span className="font-medium text-text-primary">Total Waste</span>
                    <span className="text-2xl font-bold text-emerald">
                      {WASTE_TYPES
                        .filter(t => selectedTypes[t.key])
                        .reduce((sum, t) => sum + (parseFloat(quantities[t.key]) || 0), 0)
                        .toFixed(1)} kg
                    </span>
                  </div>
                </div>
              </GlassCard>
            )}
            
            {/* Additional Details */}
            <GlassCard>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Additional Details</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <GlassInput
                  label="People Present (Optional)"
                  type="number"
                  min="0"
                  value={peoplePresent}
                  onChange={(e) => setPeoplePresent(e.target.value)}
                  placeholder={user?.account_type === 'family' ? user.family_members : 
                               user?.account_type === 'restaurant' ? user.avg_customers_per_day :
                               user.avg_daily_workers}
                />
              </div>
              
              <div className="bg-glass-white/50 rounded-glass-sm p-4">
                <h4 className="font-medium text-text-primary mb-2">Auto-filled from Profile</h4>
                <div className="grid grid-cols-2 gap-2 text-sm text-text-secondary">
                  <div><span className="font-medium">Area:</span> {user?.area || 'Not set'}</div>
                  <div><span className="font-medium">Account Type:</span> {user?.account_type}</div>
                  <div><span className="font-medium">Address:</span> {user?.address || 'Not set'}</div>
                  <div><span className="font-medium">Date:</span> {new Date().toLocaleDateString()}</div>
                  {user?.account_type === 'family' && (
                    <div><span className="font-medium">Household Members:</span> {user?.family_members}</div>
                  )}
                  {user?.account_type === 'restaurant' && (
                    <>
                      <div><span className="font-medium">Restaurant:</span> {user?.restaurant_name}</div>
                      <div><span className="font-medium">Avg Daily Customers:</span> {user?.avg_customers_per_day}</div>
                    </>
                  )}
                  {user?.account_type === 'organization' && (
                    <>
                      <div><span className="font-medium">Organization:</span> {user?.organization_name}</div>
                      <div><span className="font-medium">Avg Daily Workers:</span> {user?.avg_daily_workers}</div>
                    </>
                  )}
                </div>
              </div>
            </GlassCard>
            
            <GlassButton variant="primary" type="submit" className="w-full" loading={loading}>
              SUBMIT WASTE DATA
            </GlassButton>
          </form>
        </div>
      </div>
    )
  }
  
  // Verification Screen
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Verify Waste Data</h1>
          <p className="text-text-secondary mt-1">Please review your submission before confirming</p>
        </div>
        
        {error && (
          <div className="inline-error mb-6" role="alert">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        )}
        
        <GlassCard>
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-text-secondary">Area</p>
                <p className="font-medium text-text-primary">{submissionData.area}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">Date</p>
                <p className="font-medium text-text-primary">{new Date(submissionData.submission_date).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">Account Type</p>
                <p className="font-medium text-text-primary capitalize">{submissionData.account_type}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">People Present</p>
                <p className="font-medium text-text-primary">{submissionData.people_present || 'Auto'}</p>
              </div>
              {submissionData.family_members && (
                <div>
                  <p className="text-sm text-text-secondary">Household Members</p>
                  <p className="font-medium text-text-primary">{submissionData.family_members}</p>
                </div>
              )}
              {submissionData.customers && (
                <div>
                  <p className="text-sm text-text-secondary">Avg Daily Customers</p>
                  <p className="font-medium text-text-primary">{submissionData.customers}</p>
                </div>
              )}
            </div>
            
            <div className="border-t border-glass-border pt-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Waste Breakdown</h3>
              <div className="space-y-3">
                {submissionData.items.map((item, i) => (
                  <div key={i} className="flex justify-between py-2 border-b border-glass-border/50 last:border-0">
                    <span className="capitalize text-text-secondary">{item.waste_type}</span>
                    <span className="font-medium text-text-primary">{item.quantity_kg} kg</span>
                  </div>
                ))}
              </div>
              <div className="flex justify-between pt-4 border-t border-glass-border text-lg">
                <span className="font-semibold text-text-primary">Total</span>
                <span className="text-2xl font-bold text-emerald">{submissionData.total_waste_kg.toFixed(1)} kg</span>
              </div>
            </div>
          </div>
        </GlassCard>
        
        <div className="flex gap-4 mt-6">
          <GlassButton variant="ghost" onClick={handleEdit} className="flex-1" loading={loading}>
            EDIT
          </GlassButton>
          <GlassButton variant="primary" onClick={handleVerifySubmit} className="flex-1" loading={loading}>
            CONFIRM & SUBMIT
          </GlassButton>
        </div>
      </div>
    </div>
  )
}