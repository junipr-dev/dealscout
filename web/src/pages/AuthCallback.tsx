import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import './AuthCallback.css'

export default function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')

  useEffect(() => {
    const token = searchParams.get('token')

    if (!token) {
      setStatus('error')
      setTimeout(() => navigate('/'), 3000)
      return
    }

    // Store token in localStorage
    localStorage.setItem('ebay_access_token', token)
    setStatus('success')

    // Redirect to home after brief success message
    setTimeout(() => navigate('/'), 2000)
  }, [searchParams, navigate])

  return (
    <div className="auth-callback">
      <div className="callback-container">
        {status === 'processing' && (
          <>
            <div className="spinner"></div>
            <h2>Processing authentication...</h2>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="success-icon">✓</div>
            <h2>Authentication successful!</h2>
            <p>Redirecting to home...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="error-icon">✗</div>
            <h2>Authentication failed</h2>
            <p>No token received. Redirecting to home...</p>
          </>
        )}
      </div>
    </div>
  )
}
