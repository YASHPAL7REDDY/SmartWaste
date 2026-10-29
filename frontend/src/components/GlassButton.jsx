import { forwardRef } from 'react'
import { clsx } from 'clsx'

export const GlassButton = forwardRef(({ 
  children, 
  variant = 'default', 
  className = '', 
  disabled = false,
  loading = false,
  ...props 
}, ref) => {
  const baseClasses = 'inline-flex items-center justify-center px-6 py-3 rounded-glass-sm font-medium transition-all duration-fast focus:outline-none focus:ring-2 focus:ring-emerald/50 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variantClasses = {
    default: 'bg-glass-white-strong border border-glass-border text-text-primary hover:bg-emerald/10 hover:border-emerald/50 hover:shadow-emerald-glow',
    primary: 'bg-emerald text-matte-black hover:bg-emerald-light hover:shadow-emerald-glow-strong',
    secondary: 'bg-glass-white border border-glass-border text-text-secondary hover:bg-glass-white-strong hover:border-emerald/30',
    danger: 'bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30 hover:border-red-500 hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]',
    ghost: 'bg-transparent border border-transparent text-text-secondary hover:bg-glass-white hover:text-text-primary',
  }
  
  return (
    <button
      ref={ref}
      className={clsx(baseClasses, variantClasses[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {children}
    </button>
  )
})

GlassButton.displayName = 'GlassButton'