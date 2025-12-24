import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import './Toast.css'

export type ToastType = 'success' | 'info' | 'warning' | 'error' | 'deal' | 'sale'

interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
}

interface ToastContextType {
  showToast: (toast: Omit<Toast, 'id'>) => void
  showDealNotification: (title: string, profit?: number) => void
  showSaleNotification: (itemName: string, profit: number) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000,
    }
    setToasts(prev => [...prev, newToast])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const showDealNotification = useCallback((title: string, profit?: number) => {
    showToast({
      type: 'deal',
      title: 'New Deal Found!',
      message: profit ? `${title} • $${profit.toFixed(0)} profit potential` : title,
      duration: 6000,
    })
  }, [showToast])

  const showSaleNotification = useCallback((itemName: string, profit: number) => {
    showToast({
      type: 'sale',
      title: 'Sale Completed!',
      message: `${itemName} • +$${profit.toFixed(2)} profit`,
      duration: 8000,
    })
  }, [showToast])

  return (
    <ToastContext.Provider value={{ showToast, showDealNotification, showSaleNotification }}>
      {children}
      <div className="toast-container">
        {toasts.map(toast => (
          <ToastItem key={toast.id} toast={toast} onDismiss={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    const dismissTimer = setTimeout(() => {
      setIsExiting(true)
    }, toast.duration! - 300) // Start exit animation before removal

    const removeTimer = setTimeout(() => {
      onDismiss(toast.id)
    }, toast.duration!)

    return () => {
      clearTimeout(dismissTimer)
      clearTimeout(removeTimer)
    }
  }, [toast.id, toast.duration, onDismiss])

  const handleDismiss = () => {
    setIsExiting(true)
    setTimeout(() => onDismiss(toast.id), 300)
  }

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return '✓'
      case 'error':
        return '✕'
      case 'warning':
        return '⚠'
      case 'info':
        return 'ℹ'
      case 'deal':
        return '🔥'
      case 'sale':
        return '💰'
      default:
        return 'ℹ'
    }
  }

  return (
    <div className={`toast toast-${toast.type} ${isExiting ? 'toast-exit' : 'toast-enter'}`}>
      <div className="toast-icon">{getIcon()}</div>
      <div className="toast-content">
        <div className="toast-title">{toast.title}</div>
        {toast.message && <div className="toast-message">{toast.message}</div>}
      </div>
      <button className="toast-close" onClick={handleDismiss}>
        ✕
      </button>
      <div className="toast-progress" style={{ animationDuration: `${toast.duration}ms` }} />
    </div>
  )
}

export default ToastProvider
