import { forwardRef } from 'react'
import { clsx } from 'clsx'

export const GlassCard = forwardRef(({ 
  children, 
  className = '', 
  hover = false,
  padding = 'p-6',
  ...props 
}, ref) => {
  const baseClasses = 'bg-glass-white backdrop-blur-glass border border-glass-border rounded-glass shadow-glass transition-all duration-normal'
  
  return (
    <div
      ref={ref}
      className={clsx(
        baseClasses, 
        padding,
        hover && 'hover:bg-glass-white-strong hover:shadow-glass-hover hover:border-emerald/30 cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})

GlassCard.displayName = 'GlassCard'