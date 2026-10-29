import { forwardRef } from 'react'
import { clsx } from 'clsx'

const GlassInputInner = forwardRef(({
  label,
  error,
  className = '',
  type = 'text',
  as = 'input',
  options,
  ...props
}, ref) => {
  const inputClasses = clsx(
    'w-full px-4 py-3 rounded-glass-sm bg-glass-white border text-text-primary placeholder-text-muted',
    'focus:outline-none focus:ring-2 transition-all duration-fast',
    error
      ? 'border-red-500/50 focus:border-red-500 focus:ring-red-500/20'
      : 'border-glass-border focus:border-emerald/50 focus:ring-emerald/20',
    className
  )

  const selectClasses = clsx(
    inputClasses,
    'appearance-none bg-no-repeat bg-right pr-10',
    'bg-[url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 20 20\'%3E%3Cpath stroke=\'%23a0a0a0\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'1.5\' d=\'M6 8l4 4 4-4\'/%3E%3C/svg%3E")]'
  )

  if (as === 'select') {
    return (
      <div className="w-full">
        {label && (
          <label className="glass-label">{label}</label>
        )}
        <select
          ref={ref}
          className={selectClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${props.id}-error` : undefined}
          {...props}
        >
          {options?.map((opt, i) => (
            <option key={i} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {error && (
          <p id={`${props.id}-error`} className="mt-1.5 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="w-full">
      {label && (
        <label className="glass-label">{label}</label>
      )}
      <input
        ref={ref}
        type={type}
        className={inputClasses}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${props.id}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${props.id}-error`} className="mt-1.5 text-sm text-red-400" role="alert">
          {error}
        </p>
      )}
    </div>
  )
})

export const GlassInput = forwardRef((props, ref) => {
  return <GlassInputInner {...props} ref={ref} />
})

GlassInput.displayName = 'GlassInput'