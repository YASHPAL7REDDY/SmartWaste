import { clsx } from 'clsx'
import { GlassButton } from './GlassButton'

export function ErrorState({ 
  title = 'Something went wrong', 
  message = 'An unexpected error occurred. Please try again.', 
  onRetry,
  className = '' 
}) {
  return (
    <div className={clsx('flex flex-col items-center justify-center text-center py-16 px-4', className)}>
      <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-6 text-red-400">
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-text-primary mb-2">{title}</h3>
      <p className="text-text-secondary mb-6 max-w-md">{message}</p>
      {onRetry && (
        <GlassButton variant="primary" onClick={onRetry}>
          Try Again
        </GlassButton>
      )}
    </div>
  )
}

export function InlineError({ message, className = '' }) {
  return (
    <div className={clsx('flex items-center gap-2 p-3 rounded-glass-sm bg-red-500/10 border border-red-500/20 text-red-400 text-sm', className)}>
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{message}</span>
    </div>
  )
}