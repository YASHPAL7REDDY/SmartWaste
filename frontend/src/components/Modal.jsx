import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { clsx } from 'clsx'
import { GlassButton } from './GlassButton'

export function Modal({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'md',
  showClose = true 
}) {
  if (!isOpen) return null
  
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [onClose])
  
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-5xl',
  }
  
  const modalContent = (
    <div className="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="fixed inset-0 bg-matte-black/80 backdrop-blur-sm transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
        <div className={clsx('relative w-full animate-in', sizeClasses[size])}>
          <div className="glass-card">
            <div className="flex items-center justify-between mb-6">
              <h2 id="modal-title" className="text-xl font-semibold text-text-primary">
                {title}
              </h2>
              {showClose && (
                <button
                  onClick={onClose}
                  className="glass-button ghost p-2 rounded-full hover:bg-red-500/10 hover:text-red-400"
                  aria-label="Close modal"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            {children}
          </div>
        </div>
      </div>
    </div>
  )
  
  return createPortal(modalContent, document.body)
}

export function ConfirmModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'primary',
  loading = false 
}) {
  if (!isOpen) return null
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <p className="text-text-secondary mb-6">{message}</p>
      <div className="flex gap-3 justify-end">
        <GlassButton variant="ghost" onClick={onClose} disabled={loading}>
          {cancelText}
        </GlassButton>
        <GlassButton variant={variant} onClick={onConfirm} loading={loading}>
          {confirmText}
        </GlassButton>
      </div>
    </Modal>
  )
}