import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { GlassButton, GlassCard, GlassInput } from '../components'

export function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  
  const [role, setRole] = useState('user')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      await login(email, password, role)
      if (role === 'user') navigate('/dashboard')
      else if (role === 'collector') navigate('/collector')
      else if (role === 'admin') navigate('/admin')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  const roles = [
    { value: 'user', label: 'USER', desc: 'Residents, restaurants, organizations' },
    { value: 'collector', label: 'COLLECTOR', desc: 'Waste collection staff' },
    { value: 'admin', label: 'ADMIN', desc: 'System administrators' },
  ]
  
  return (
    <div className="page-container flex min-h-screen items-center justify-center py-20">
      <div className="w-full max-w-md px-4 animate-in">
        <GlassCard padding="p-8">
          <div className="text-center mb-8">
            <Link to="/" className="inline-block mb-6">
              <span className="text-3xl font-bold text-emerald tracking-tight">SMARTWASTE</span>
            </Link>
            <h1 className="text-2xl font-bold text-text-primary mb-2">Welcome Back</h1>
            <p className="text-text-secondary">Sign in to your account</p>
          </div>
          
          <div className="mb-6">
            <label className="glass-label">Account Type</label>
            <div className="grid grid-cols-3 gap-3">
              {roles.map((r) => (
                <button
                  key={r.value}
                  onClick={() => setRole(r.value)}
                  className={`
                    relative p-4 rounded-glass-sm border transition-all duration-fast
                    ${role === r.value 
                      ? 'border-emerald/50 bg-emerald/5 text-text-primary' 
                      : 'border-glass-border bg-glass-white text-text-secondary hover:border-emerald/30 hover:bg-emerald/5'
                    }
                  `}
                >
                  <div className="font-semibold text-sm">{r.label}</div>
                  <div className="text-xs text-text-muted mt-1">{r.desc}</div>
                </button>
              ))}
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <GlassInput
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
            
            <GlassInput
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
            
            {error && (
              <div className="inline-error" role="alert">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{error}</span>
              </div>
            )}
            
            <GlassButton variant="primary" type="submit" className="w-full" loading={loading}>
              SIGN IN
            </GlassButton>
          </form>
          
          <div className="mt-8 pt-6 border-t border-glass-border">
            <p className="text-center text-text-secondary mb-4">
              Don't have an account?{' '}
              <Link to="/register" className="text-emerald hover:underline font-medium">
                Create Account
              </Link>
            </p>
            <p className="text-center text-xs text-text-muted">
              Collector and Admin accounts are created by administrators.
            </p>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}