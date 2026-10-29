import { useState, useEffect } from 'react'

export function PageTransition({ children, className = '' }) {
  const [isMounted, setIsMounted] = useState(false)
  const [isExiting, setIsExiting] = useState(false)
  
  useEffect(() => {
    setIsMounted(true)
    return () => {
      setIsExiting(true)
    }
  }, [])
  
  if (!isMounted) {
    return (
      <div className={className} style={{ opacity: 0 }}>
        {children}
      </div>
    )
  }
  
  return (
    <div 
      className={className}
      style={{
        opacity: isExiting ? 0 : 1,
        transform: isExiting ? 'translateY(10px)' : 'translateY(0)',
        transition: 'opacity 0.2s ease-out, transform 0.2s ease-out',
      }}
    >
      {children}
    </div>
  )
}

export function AnimatePresence({ children, mode = 'wait' }) {
  return children
}