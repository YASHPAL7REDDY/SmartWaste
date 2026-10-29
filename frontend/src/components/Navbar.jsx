import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { useAuth } from '../context/AuthContext'
import { GlassButton } from './GlassButton'

const userNavigation = [
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'About', href: '/about' },
  { name: 'Collect Data', href: '/collect' },
  { name: 'My Data', href: '/my-data' },
  { name: 'Predictions', href: '/predictions' },
  { name: 'Profile', href: '/profile' },
]

const collectorNavigation = [
  { name: 'Dashboard', href: '/collector' },
  { name: 'Collections', href: '/collector/collections' },
  { name: 'Vehicle', href: '/collector/vehicle' },
  { name: 'Facilities', href: '/collector/facilities' },
]

const adminNavigation = [
  { name: 'Dashboard', href: '/admin' },
  { name: 'Analytics', href: '/admin/analytics' },
  { name: 'ML Performance', href: '/admin/ml-performance' },
  { name: 'Facilities', href: '/admin/facilities' },
  { name: 'Collectors', href: '/admin/collectors' },
]

export function Navbar() {
  const { user, isAuthenticated, isAdmin, isCollector, isUser, role, logout } = useAuth()
  const location = useLocation()
  
  let userNav = []
  if (isAdmin) userNav = adminNavigation
  else if (isCollector) userNav = collectorNavigation
  else if (isUser) userNav = userNavigation
  
  if (!isAuthenticated) {
    return (
      <nav className="fixed top-0 left-0 right-0 z-40 glass-card border-b border-glass-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="text-2xl font-bold text-emerald tracking-tight">
              SMARTWASTE
            </Link>
            <Link to="/login">
              <GlassButton variant="primary">Login</GlassButton>
            </Link>
          </div>
        </div>
      </nav>
    )
  }
  
  return (
    <nav className="fixed top-0 left-0 right-0 z-40 glass-card border-b border-glass-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to={role === 'user' ? '/dashboard' : role === 'collector' ? '/collector' : '/admin'} className="text-2xl font-bold text-emerald tracking-tight">
            SMARTWASTE
          </Link>
          
          <div className="hidden md:flex items-center gap-6">
            {userNav.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'text-sm font-medium transition-colors duration-fast',
                  location.pathname === item.href
                    ? 'text-emerald'
                    : 'text-text-secondary hover:text-text-primary'
                )}
              >
                {item.name}
              </Link>
            ))}
          </div>
          
          <div className="flex items-center gap-4">
            <span className="hidden sm:block text-sm text-text-secondary">
              {user?.name}
            </span>
            <GlassButton variant="ghost" size="sm" onClick={logout}>
              Logout
            </GlassButton>
          </div>
        </div>
      </div>
    </nav>
  )
}