import { clsx } from 'clsx'

export function LoadingState({ 
  size = 'md', 
  className = '',
  text = 'Loading...' 
}) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }
  
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-4 py-12', className)}>
      <div
        className={clsx(
          'rounded-full border-emerald/20 border-t-emerald animate-spin',
          sizeClasses[size]
        )}
        role="status"
        aria-label={text}
      />
      <p className="text-text-secondary text-sm">{text}</p>
    </div>
  )
}

export function InlineLoading({ size = 'sm' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-5 h-5 border-2',
  }
  
  return (
    <div
      className={clsx(
        'inline-block rounded-full border-emerald/20 border-t-emerald animate-spin',
        sizeClasses[size]
      )}
      role="status"
      aria-label="Loading"
    />
  )
}

export function PageLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-matte-black">
      <LoadingState size="lg" text="Loading SmartWaste..." />
    </div>
  )
}