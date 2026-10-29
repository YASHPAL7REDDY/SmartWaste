import { clsx } from 'clsx'
import { GlassButton } from './GlassButton'

export function EmptyState({ 
  icon, 
  title, 
  description, 
  action,
  className = '' 
}) {
  return (
    <div className={clsx('flex flex-col items-center justify-center text-center py-16 px-4', className)}>
      <div className="w-16 h-16 rounded-full bg-glass-white-strong flex items-center justify-center mb-6 text-text-muted">
        {icon}
      </div>
      <h3 className="text-lg font-medium text-text-primary mb-2">{title}</h3>
      <p className="text-text-secondary mb-6 max-w-md">{description}</p>
      {action && (
        <GlassButton variant="primary" onClick={action.onClick}>
          {action.label}
        </GlassButton>
      )}
    </div>
  )
}

export function NoDataState({ message = 'No data available yet.' }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      }
      title="No Data"
      description={message}
    />
  )
}