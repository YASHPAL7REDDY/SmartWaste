import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { GlassButton, GlassCard, GlassInput } from '../components'

const accountTypes = [
  { value: 'family', label: 'FAMILY', icon: '👨‍👩‍👧‍👦', desc: 'Residential households' },
  { value: 'restaurant', label: 'RESTAURANT', icon: '🍽️', desc: 'Food service establishments' },
  { value: 'organization', label: 'ORGANIZATION', icon: '🏢', desc: 'Companies, offices, institutions' },
]

export function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  
  const [accountType, setAccountType] = useState('family')
  const [step, setStep] = useState(1) // 1 = account type, 2 = form
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    mobile: '',
    password: '',
    confirmPassword: '',
    area: '',
    address: '',
    city: '',
    pincode: '',
    familyMembers: '',
    restaurantName: '',
    gstin: '',
    avgCustomersPerDay: '',
    organizationName: '',
    avgDailyWorkers: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitError, setSubmitError] = useState('')
  
  const validateEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  }
  
  const validateMobile = (mobile) => {
    return /^[6-9]\d{9}$/.test(mobile)
  }
  
  const validatePassword = (password) => {
    if (!password || password.length < 8) return 'Password must be at least 8 characters'
    if (!/[A-Z]/.test(password)) return 'Password must contain at least one uppercase letter'
    if (!/[a-z]/.test(password)) return 'Password must contain at least one lowercase letter'
    if (!/[0-9]/.test(password)) return 'Password must contain at least one number'
    return ''
  }
  
  const validateGSTIN = (gstin) => {
    if (!gstin) return ''
    return /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(gstin) ? '' : 'Invalid GSTIN format'
  }
  
  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }
  
  const validateStep1 = () => {
    const newErrors = {}
    
    if (!formData.name?.trim()) newErrors.name = 'Name is required'
    if (!formData.email?.trim()) newErrors.email = 'Email is required'
    else if (!validateEmail(formData.email)) newErrors.email = 'Invalid email format'
    if (!formData.mobile?.trim()) newErrors.mobile = 'Mobile number is required'
    else if (!validateMobile(formData.mobile)) newErrors.mobile = 'Invalid mobile number (10 digits starting with 6-9)'
    if (!formData.password) newErrors.password = 'Password is required'
    else {
      const pwdError = validatePassword(formData.password)
      if (pwdError) newErrors.password = pwdError
    }
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = 'Passwords do not match'
    if (!formData.area?.trim()) newErrors.area = 'Area is required'
    if (!formData.address?.trim()) newErrors.address = 'Address is required'
    if (!formData.city?.trim()) newErrors.city = 'City is required'
    if (!formData.pincode?.trim()) newErrors.pincode = 'Pincode is required'
    else if (!/^\d{6}$/.test(formData.pincode)) newErrors.pincode = 'Pincode must be 6 digits'
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
  
  const validateStep2 = () => {
    const newErrors = {}
    
    if (accountType === 'family') {
      if (!formData.familyMembers || parseInt(formData.familyMembers) < 1) {
        newErrors.familyMembers = 'Number of household members is required (minimum 1)'
      }
    } else if (accountType === 'restaurant') {
      if (!formData.restaurantName?.trim()) newErrors.restaurantName = 'Restaurant name is required'
      if (!formData.avgCustomersPerDay || parseInt(formData.avgCustomersPerDay) < 0) {
        newErrors.avgCustomersPerDay = 'Average daily customers is required'
      }
      const gstinError = validateGSTIN(formData.gstin)
      if (gstinError) newErrors.gstin = gstinError
    } else if (accountType === 'organization') {
      if (!formData.organizationName?.trim()) newErrors.organizationName = 'Organization name is required'
      if (!formData.avgDailyWorkers || parseInt(formData.avgDailyWorkers) < 1) {
        newErrors.avgDailyWorkers = 'Average daily workers is required (minimum 1)'
      }
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
  
  const handleBack = () => {
    setStep(1)
    setErrors({})
  }
  
  const handleNext = () => {
    if (validateStep1()) {
      setStep(2)
      setErrors({})
    }
  }
  
  const handleSubmit = async (e) => {
e.preventDefault()
    setSubmitError('')
    
    if (!validateStep2()) return
    
    setLoading(true)
    
    try {
      const userData = {
        name: formData.name,
        email: formData.email,
        mobile: formData.mobile,
        password: formData.password,
        account_type: accountType,
        area: formData.area,
        address: formData.address,
        city: formData.city,
        pincode: formData.pincode,
      }
      
      if (accountType === 'family') {
        userData.family_members = parseInt(formData.familyMembers)
      } else if (accountType === 'restaurant') {
        userData.restaurant_name = formData.restaurantName
        userData.gstin = formData.gstin
        userData.avg_customers_per_day = parseInt(formData.avgCustomersPerDay)
      } else if (accountType === 'organization') {
        userData.organization_name = formData.organizationName
        userData.avg_daily_workers = parseInt(formData.avgDailyWorkers)
      }
      
      await register(userData)
      navigate('/dashboard')
    } catch (err) {
      const detail = err.response?.data?.detail
      let errorMessage = 'Registration failed. Please try again.'
      if (typeof detail === 'string') {
        errorMessage = detail
      } else if (Array.isArray(detail)) {
        errorMessage = detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ')
      } else if (detail && typeof detail === 'object') {
        errorMessage = detail.message || detail.error || JSON.stringify(detail)
      }
      setSubmitError(errorMessage)
    } finally {
      setLoading(false)
    }
  }
  
  // Step 1: Common fields
  if (step === 1) {
    return (
      <div className="page-container flex min-h-screen items-center justify-center py-20">
        <div className="w-full max-w-4xl px-4 animate-in">
          <GlassCard padding="p-8">
            <div className="text-center mb-8">
              <Link to="/" className="inline-block mb-6">
                <span className="text-3xl font-bold text-emerald tracking-tight">SMARTWASTE</span>
              </Link>
              <h1 className="text-2xl font-bold text-text-primary mb-2">Create Account</h1>
              <p className="text-text-secondary">Select your account type to continue</p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 mb-8">
              {accountTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => {
                    setAccountType(type.value)
                    setStep(2)
                  }}
                  className={`
                    relative p-6 rounded-glass border transition-all duration-fast text-left
                    ${accountType === type.value 
                      ? 'border-emerald/50 bg-emerald/5' 
                      : 'border-glass-border bg-glass-white hover:border-emerald/30 hover:bg-emerald/5'
                    }
                  `}
                >
                  <div className="text-3xl mb-2">{type.icon}</div>
                  <div className="font-semibold text-text-primary">{type.label}</div>
                  <div className="text-sm text-text-secondary mt-1">{type.desc}</div>
                </button>
              ))}
            </div>
            
            <div className="text-center text-sm text-text-muted">
              By creating an account, you agree to our Terms of Service and Privacy Policy
            </div>
          </GlassCard>
        </div>
      </div>
    )
  }
  
  // Step 2: Account-specific form
  return (
    <div className="page-container flex min-h-screen items-center justify-center py-12">
      <div className="w-full max-w-2xl px-4 animate-in">
        <GlassCard padding="p-8">
          <div className="flex items-center justify-between mb-6">
            <button onClick={handleBack} className="glass-button ghost p-2 rounded-full" aria-label="Back">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div className="flex-1 text-center">
              <span className="text-sm font-medium text-emerald">{accountTypes.find(t => t.value === accountType)?.label}</span>
            </div>
            <div className="w-10" />
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Common fields */}
            <GlassInput
              label="Full Name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="John Doe"
              error={errors.name}
              required
              autoComplete="name"
            />
            
            <GlassInput
              label="Email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="you@example.com"
              error={errors.email}
              required
              autoComplete="email"
            />
            
            <GlassInput
              label="Mobile Number"
              type="tel"
              name="mobile"
              value={formData.mobile}
              onChange={handleInputChange}
              placeholder="9876543210"
              error={errors.mobile}
              required
              autoComplete="tel"
              maxLength={10}
            />
            
            <GlassInput
              label="Password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="••••••••"
              error={errors.password}
              required
              autoComplete="new-password"
            />
            
            <GlassInput
              label="Confirm Password"
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              placeholder="••••••••"
              error={errors.confirmPassword}
              required
              autoComplete="new-password"
            />
            
            <GlassInput
              label="Area"
              name="area"
              value={formData.area}
              onChange={handleInputChange}
              placeholder="e.g., Whitefield, Koramangala"
              error={errors.area}
              required
            />
            
            <GlassInput
              label="Address"
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              placeholder="Street, Building, Floor"
              error={errors.address}
              required
            />
            
            <div className="grid grid-cols-2 gap-4">
              <GlassInput
                label="City"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                placeholder="Bengaluru"
                error={errors.city}
                required
              />
              
              <GlassInput
                label="Pincode"
                name="pincode"
                value={formData.pincode}
                onChange={handleInputChange}
                placeholder="560001"
                error={errors.pincode}
                required
                maxLength={6}
              />
            </div>
            
            {/* Account-specific fields */}
            {accountType === 'family' && (
              <GlassInput
                label="Number of Household Members"
                type="number"
                name="familyMembers"
                value={formData.familyMembers}
                onChange={handleInputChange}
                placeholder="3"
                error={errors.familyMembers}
                required
                min={1}
              />
            )}
            
            {accountType === 'restaurant' && (
              <>
                <GlassInput
                  label="Restaurant Name"
                  name="restaurantName"
                  value={formData.restaurantName}
                  onChange={handleInputChange}
                  placeholder="Tasty Bites"
                  error={errors.restaurantName}
                  required
                />
                
                <GlassInput
                  label="GSTIN (Optional)"
                  name="gstin"
                  value={formData.gstin}
                  onChange={handleInputChange}
                  placeholder="29ABCDE1234F1Z5"
                  error={errors.gstin}
                  maxLength={15}
                />
                
                <GlassInput
                  label="Average Daily Customers"
                  type="number"
                  name="avgCustomersPerDay"
                  value={formData.avgCustomersPerDay}
                  onChange={handleInputChange}
                  placeholder="150"
                  error={errors.avgCustomersPerDay}
                  required
                  min={0}
                />
              </>
            )}
            
            {accountType === 'organization' && (
              <>
                <GlassInput
                  label="Organization Name"
                  name="organizationName"
                  value={formData.organizationName}
                  onChange={handleInputChange}
                  placeholder="TechCorp Solutions"
                  error={errors.organizationName}
                  required
                />
                
                <GlassInput
                  label="Average Daily Workers"
                  type="number"
                  name="avgDailyWorkers"
                  value={formData.avgDailyWorkers}
                  onChange={handleInputChange}
                  placeholder="50"
                  error={errors.avgDailyWorkers}
                  required
                  min={1}
                />
              </>
            )}
            
            {submitError && (
              <div className="inline-error" role="alert">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{submitError}</span>
              </div>
            )}
            
            <div className="flex gap-3 pt-4">
              <GlassButton variant="ghost" type="button" onClick={handleBack} className="flex-1">
                BACK
              </GlassButton>
              <GlassButton variant="primary" type="submit" className="flex-1" loading={loading}>
                CREATE ACCOUNT
              </GlassButton>
            </div>
          </form>
          
          <p className="mt-6 text-center text-sm text-text-muted">
            Already have an account?{' '}
            <Link to="/login" className="text-emerald hover:underline font-medium">
              Login
            </Link>
          </p>
        </GlassCard>
      </div>
    </div>
  )
}