import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { GlassCard, GlassButton, GlassInput, Navbar } from '../components'

export function Profile() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  
  const handleLogout = () => {
    // Logout handled by Navbar
  }
  
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-2xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary">Profile</h1>
          <p className="text-text-secondary mt-1">Manage your account settings</p>
        </div>
        
        {message && (
          <div className={`inline-error mb-6 ${message.startsWith('Error') ? '' : 'bg-green-500/10 border-green-500/20 text-green-400'}`} role="alert">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={message.startsWith('Error') ? "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" : "M5 13l4 4L19 7"} />
            </svg>
            <span>{message}</span>
          </div>
        )}
        
        <GlassCard>
          <h2 className="text-lg font-semibold text-text-primary mb-6">Account Information</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <GlassInput label="Full Name" value={user?.name} disabled />
              <GlassInput label="Email" type="email" value={user?.email} disabled />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <GlassInput label="Mobile" value={user?.mobile} disabled />
              <GlassInput label="Account Type" value={user?.account_type} disabled />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <GlassInput label="Area" value={user?.area || 'Not set'} disabled />
              <GlassInput label="City" value={user?.city || 'Not set'} disabled />
            </div>
            
            <GlassInput label="Address" value={user?.address || 'Not set'} disabled />
            
            {user?.account_type === 'family' && (
              <GlassInput label="Household Members" value={user?.family_members?.toString() || 'Not set'} disabled />
            )}
            
            {user?.account_type === 'restaurant' && (
              <div className="grid grid-cols-2 gap-4">
                <GlassInput label="Restaurant Name" value={user?.restaurant_name || 'Not set'} disabled />
                <GlassInput label="Avg Daily Customers" value={user?.avg_customers_per_day?.toString() || 'Not set'} disabled />
              </div>
            )}
            
            {user?.account_type === 'organization' && (
              <div className="grid grid-cols-2 gap-4">
                <GlassInput label="Organization Name" value={user?.organization_name || 'Not set'} disabled />
                <GlassInput label="Avg Daily Workers" value={user?.employee_count?.toString() || 'Not set'} disabled />
              </div>
            )}
            
            <div className="pt-4 border-t border-glass-border">
              <p className="text-sm text-text-secondary mb-4">Account created: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}</p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard className="mt-6 border-red-500/30">
          <h2 className="text-lg font-semibold text-text-primary mb-4">Danger Zone</h2>
          <p className="text-text-secondary mb-4">Once you delete your account, there is no going back. Please be certain.</p>
          <GlassButton variant="danger" onClick={() => setMessage('Error: Account deletion not implemented yet')}>
            Delete Account
          </GlassButton>
        </GlassCard>
      </div>
    </div>
  )
}