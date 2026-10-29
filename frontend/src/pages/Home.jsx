import { Link } from 'react-router-dom'
import { GlassButton, GlassCard } from '../components'

export function Home() {
  return (
    <div className="page-container flex min-h-screen items-center justify-center">
      <div className="max-w-3xl w-full px-6 text-center animate-in">
        <div className="mb-12">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-2xl bg-emerald/10 border border-emerald/30 mb-8 animate-pulse-glow">
            <svg className="w-12 h-12 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-text-primary mb-6">
            SMARTWASTE
          </h1>
          
          <p className="text-xl sm:text-2xl text-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed">
            AI-POWERED WASTE MANAGEMENT
          </p>
          
          <p className="text-lg text-text-secondary mb-16 max-w-xl mx-auto leading-relaxed">
            Predict. Prevent. Collect. Recycle.
          </p>
        </div>
        
        <Link to="/login">
          <GlassButton variant="primary" className="w-full sm:w-auto px-12 py-4 text-lg">
            LOGIN
          </GlassButton>
        </Link>
        
        <div className="mt-20 grid grid-cols-3 gap-6 text-center">
          {[
            { icon: '🔮', label: 'ML Predictions', desc: 'Next-day waste forecasting' },
            { icon: '♻️', label: 'Smart Collection', desc: 'Optimized routing & capacity' },
            { icon: '📊', label: 'Real Analytics', desc: 'Live dashboards & insights' },
          ].map((item, i) => (
            <GlassCard key={i} hover padding="p-6">
              <div className="text-3xl mb-3">{item.icon}</div>
              <h3 className="font-semibold text-text-primary mb-1">{item.label}</h3>
              <p className="text-sm text-text-secondary">{item.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </div>
  )
}