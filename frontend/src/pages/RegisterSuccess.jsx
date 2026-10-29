import { Link } from 'react-router-dom'
import { GlassButton, GlassCard } from '../components'

export function RegisterSuccess() {
  return (
    <div className="page-container flex min-h-screen items-center justify-center">
      <div className="max-w-md w-full px-6 text-center animate-in">
        <GlassCard padding="p-10">
          <div className="w-20 h-20 rounded-full bg-emerald/10 border border-emerald/30 flex items-center justify-center mx-auto mb-8 animate-pulse-glow">
            <svg className="w-10 h-10 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-text-primary mb-4">Account Created Successfully</h1>
          
          <p className="text-text-secondary mb-8">
            Your account has been created. You can now log in to start using SmartWaste.
          </p>
          
          <Link to="/login">
            <GlassButton variant="primary" className="w-full">
              RETURN TO LOGIN
            </GlassButton>
          </Link>
        </GlassCard>
      </div>
    </div>
  )
}